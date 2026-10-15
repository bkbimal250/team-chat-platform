"""Local-only real Gateway contact smoke. No providers; credentials remain in .local/."""
import asyncio
import json
import secrets
import sys
from pathlib import Path
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import httpx
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.models import Identity
from scripts.local import dev

async def main():
    assert dev.env("identity")["APP_ENV"]=="development"
    assert dev.env("identity")["OTP_PROVIDER"]=="development"
    fixture=dev.LOCAL/"contact-smoke-accounts.json"
    if fixture.exists():
        accounts=json.loads(fixture.read_text())
    else:
        async with SessionLocal() as s:
            used=set((await s.scalars(select(Identity.phone_number))).all())
        available=["+120255501"+str(i).zfill(2) for i in range(100) if "+120255501"+str(i).zfill(2) not in used]
        assert len(available)>=6
        accounts={}
        for name,phone in zip("ABCDE",available):
            suffix=uuid4().hex
            accounts[name]={"email":"contact-smoke-"+suffix+"@example.test","password":secrets.token_urlsafe(24),"phone":phone,"device":{"installation_id":suffix,"platform":"WEB","device_name":"Contact smoke"},"display_name":"Contact test "+name}
        accounts["unknown"]=available[5]
        fixture.write_text(json.dumps(accounts))
    assertions=0
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8008",timeout=30) as client:
        async def call(method,path,token=None,payload=None,expected=200):
            nonlocal assertions
            response=await client.request(method,path,headers={"Authorization":"Bearer "+token} if token else {},json=payload)
            assert response.status_code==expected,f"{method} {path}: status {response.status_code}, expected {expected}"
            assertions+=1
            return response.json()
        tokens={}; profiles={}
        for name in "ABCDE":
            row=accounts[name]
            if not row.get("created"):
                payload={k:v for k,v in row.items() if k!="created"}
                route="personal"
                if name=="E":
                    payload["owner_name"]=payload.pop("display_name")
                    payload["company_name"]="Contact smoke workspace"
                    route="company"
                await call("POST","/api/v1/auth/registration/"+route,payload=payload,expected=201)
                row["created"]=True
                fixture.write_text(json.dumps(accounts))
            login=await call("POST","/api/v1/auth/login",payload={k:row[k] for k in ("email","password","device")})
            tokens[name]=login["access_token"]
            if name!="E":
                assert login["organization_id"] is None and login["member_id"] is None
            else:
                assert login["organization_id"] and login["member_id"]
            profiles[name]=await call("GET","/api/v1/users/me",tokens[name])
        a=tokens["A"]
        await call("GET","/api/v1/users/search?q=Contact",a,expected=403)
        await call("PATCH","/api/v1/users/me/privacy",tokens["C"],{"discoverable":False})
        await call("POST","/api/v1/users/"+profiles["A"]["user_id"]+"/block",tokens["D"],{})
        before=await call("GET","/api/v1/organizations/current/",tokens["E"])
        saved=await call("POST","/api/v1/contacts",a,{"phone":accounts["B"]["phone"],"local_label":"Only A knows this label"})
        assert saved["matched_user"]["user_id"]==profiles["B"]["user_id"]
        assert set(saved["matched_user"])=={"user_id","display_name","avatar_media_id","phone_verified"}
        assert saved["matched_user"]["phone_verified"] is False
        for name in ("C","D","unknown"):
            phone=accounts[name]["phone"] if name!="unknown" else accounts["unknown"]
            result=await call("POST","/api/v1/contacts/match",a,{"contacts":[{"phone":phone}]})
            assert result=={"results":[{"input_index":0,"matched_user":None}]}
        await call("GET","/api/v1/contacts/"+saved["id"],tokens["B"],expected=404)
        await call("PATCH","/api/v1/contacts/"+saved["id"],tokens["B"],{"local_label":"forbidden"},expected=404)
        assert "Only A knows" not in json.dumps(await call("GET","/api/v1/contacts",tokens["B"]))
        company_contact=await call("POST","/api/v1/contacts",tokens["E"],{"phone":accounts["B"]["phone"],"local_label":"E private label"})
        assert company_contact["id"]!=saved["id"] and company_contact["matched_user"]["user_id"]==profiles["B"]["user_id"]
        assert before==await call("GET","/api/v1/organizations/current/",tokens["E"])
        assert (await call("GET","/api/v1/users/me",tokens["B"]))["display_name"]=="Contact test B"
        await call("GET","/api/v1/contacts?owner_id="+profiles["B"]["user_id"],a,expected=422)
        await call("DELETE","/api/v1/contacts/"+saved["id"],a)
        await call("DELETE","/api/v1/contacts/"+company_contact["id"],tokens["E"])
        for token in tokens.values():
            await call("POST","/api/v1/auth/logout",token,{})
    print(f"Contact local E2E: PASS ({assertions} real Gateway responses; A/B personal, C hidden, D blocking, E company).")
    print("Providers called: NO. Secrets/phones/tokens printed: NO.")

if __name__=="__main__":
    asyncio.run(main())
