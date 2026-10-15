"""Real local personal-chat smoke. Never prints credentials or signed URLs."""
import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4
import httpx
import websockets
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.local import dev

async def main():
    assert dev.env("identity")["OTP_PROVIDER"] == "development"
    accounts = json.loads((dev.LOCAL / "contact-smoke-accounts.json").read_text())
    count = 0
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8008",timeout=30) as client:
        async def call(method,path,token=None,body=None,expected=200):
            nonlocal count
            r = await client.request(method,path,headers={"Authorization":"Bearer "+token} if token else {},json=body)
            assert r.status_code == expected, f"{method} {path}: HTTP {r.status_code}, expected {expected}"
            count += 1
            return r.json()
        tokens={}; profiles={}
        for name in "ABCE":
            row=accounts[name]
            result=await call("POST","/api/v1/auth/login",body={k:row[k] for k in ("email","password","device")})
            tokens[name]=result["access_token"]
            if name != "E": assert result["organization_id"] is None
            profiles[name]=await call("GET","/api/v1/users/me",tokens[name])
        a,b,c=[tokens[x] for x in "ABC"]
        saved=await call("POST","/api/v1/contacts",a,{"phone":accounts["B"]["phone"]})
        reverse=await call("POST","/api/v1/contacts",b,{"phone":accounts["A"]["phone"]})
        results=await asyncio.gather(*[call("POST","/api/v1/conversations/personal/direct",token,{"contact_id":contact},201) for token,contact in [(a,saved["id"]),(b,reverse["id"]),(a,saved["id"])]])
        cid=results[0]["id"]
        assert {r["id"] for r in results} == {cid}
        for token in (a,b):
            assert cid in {r["id"] for r in await call("GET","/api/v1/conversations",token)}
        await call("GET","/api/v1/conversations/"+cid,c,expected=404)
        await call("POST","/api/v1/conversations/personal/direct",c,{"contact_id":saved["id"]},404)
        await call("POST","/api/v1/conversations/personal/direct",a,{"identity_id":profiles["B"]["user_id"]},422)
        path="/api/v1/conversations/"+cid
        async def frame(ws,kind):
            async with asyncio.timeout(20):
                while True:
                    data=json.loads(await ws.recv())
                    if data["type"]==kind: return data
        async with websockets.connect("ws://127.0.0.1:8007/api/v1/realtime?token="+a) as wa, websockets.connect("ws://127.0.0.1:8007/api/v1/realtime?token="+b) as wb:
            for ws in (wa,wb):
                await ws.send(json.dumps({"version":1,"type":"subscribe","conversation_id":cid}))
                await frame(ws,"subscribe.ok")
            # Wait for asynchronous conversation projection; no repeat send on success.
            for _ in range(20):
                ready=await client.get(path+"/messages",headers={"Authorization":"Bearer "+a})
                if ready.status_code==200: break
                await asyncio.sleep(.5)
            message=await call("POST",path+"/messages",a,{"type":"TEXT","text":"Personal chat smoke","client_message_id":str(uuid4())})
            assert (await frame(wb,"message.created.v1"))["payload"]["message_id"]==message["id"]
            reply=await call("POST",path+"/messages",b,{"type":"TEXT","text":"Personal reply","client_message_id":str(uuid4())})
            while (await frame(wa,"message.created.v1"))["payload"]["message_id"]!=reply["id"]: pass
            await wa.send(json.dumps({"version":1,"type":"typing.start","conversation_id":cid}))
            assert (await frame(wb,"typing.updated.v1"))["payload"]["active"]
            await call("POST",path+"/delivered",b,{"sequence":reply["sequence"]})
            await frame(wa,"message.delivered.v1")
            await call("POST",path+"/read",b,{"sequence":reply["sequence"]})
            await frame(wa,"message.read.v1")
            await call("PATCH","/api/v1/messages/"+message["id"],a,{"text":"Edited smoke"})
            await call("POST","/api/v1/messages/"+message["id"]+"/reactions",b,{"reaction":"👍"})
            await call("GET",path+"/messages",c,expected=403)
            assert any(row["id"]==message["id"] for row in await call("GET",path+"/messages?limit=50",b))
        for category,mime,kind in [("image","image/png","IMAGE"),("document","application/pdf","DOCUMENT"),("audio","audio/webm","VOICE"),("video","video/mp4","VIDEO")]:
            content=b"local participant authorization fixture"
            upload=await call("POST","/api/v1/media/uploads",a,{"conversation_id":cid,"filename":"smoke.bin","mime_type":mime,"size_bytes":len(content),"media_type":category},201)
            put=await client.put(upload["upload_url"],content=content,headers=upload["required_headers"])
            assert put.status_code in (200,204)
            await call("POST","/api/v1/media/"+upload["media_id"]+"/complete",a,{})
            await call("GET","/api/v1/media/"+upload["media_id"]+"/download",c,expected=403)
            for attempt in range(20):
                response=await client.post(path+"/messages",headers={"Authorization":"Bearer "+a},json={"type":kind,"media_id":upload["media_id"],"client_message_id":str(uuid4())})
                if response.status_code==200: break
                assert response.status_code in (403,409), "media message unexpected status"
                await asyncio.sleep(.5)
            assert response.status_code==200, "media projection missing"
            # Recipients can download only after the message reference is projected.
            for _ in range(20):
                download=await client.get("/api/v1/media/"+upload["media_id"]+"/download",headers={"Authorization":"Bearer "+b})
                if download.status_code==200: break
                assert download.status_code==403
                await asyncio.sleep(.5)
            assert download.status_code==200, "media reference projection missing"
            downloaded=await client.get(download.json()["download_url"])
            assert downloaded.content==content
        print("Local image/document/voice/video upload-download and attachment authorization PASS")
        # Reconnect and simultaneous sockets use the same personal participant authorization.
        async with websockets.connect("ws://127.0.0.1:8007/api/v1/realtime?token="+b) as first, websockets.connect("ws://127.0.0.1:8007/api/v1/realtime?token="+b) as second:
            for ws in (first,second):
                await ws.send(json.dumps({"version":1,"type":"subscribe","conversation_id":cid}))
                await frame(ws,"subscribe.ok")
            message=await call("POST",path+"/messages",a,{"type":"TEXT","text":"Reconnect and multiple sockets","client_message_id":str(uuid4())})
            # Reconnecting the same session/device deliberately replaces its old socket.
            assert (await frame(second,"message.created.v1"))["payload"]["message_id"]==message["id"]
        for attempt in range(20):
            rows=await call("GET","/api/v1/conversations",b)
            summary=next(row for row in rows if row["id"]==cid)
            if summary["unread_count"]>0 and summary["last_message_preview"]==message["text"]: break
            await asyncio.sleep(.5)
        assert summary["unread_count"]>0 and summary["last_message_preview"]==message["text"]
        await call("DELETE","/api/v1/messages/"+message["id"],a)
        await call("POST","/api/v1/users/"+profiles["A"]["user_id"]+"/block",b,{})
        try:
            await call("POST",path+"/messages",a,{"type":"TEXT","text":"Must be rejected","client_message_id":str(uuid4())},403)
            await call("POST","/api/v1/conversations/personal/direct",a,{"contact_id":saved["id"]},404)
        finally:
            await call("DELETE","/api/v1/users/"+profiles["A"]["user_id"]+"/block",b)
        await call("GET","/api/v1/organizations/current/",tokens["E"])
        assert cid not in {r["id"] for r in await call("GET","/api/v1/conversations",tokens["E"])}
        for token in tokens.values(): await call("POST","/api/v1/auth/logout",token,{})
        print(f"Personal chat local smoke: {count} API assertions PASS; live messages/typing/receipts PASS.")
if __name__ == "__main__": asyncio.run(main())
