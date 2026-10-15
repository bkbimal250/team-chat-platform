import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiRequest } from "@/lib/api/client";
import { inspectFile, putFile, uploadAttachment, validateAttachment } from "@/features/media/api";
import { MediaContent } from "@/features/media/media-content";
import { VoiceRecorder } from "@/features/media/voice-recorder";
import { AttachmentComposer } from "@/features/media/attachment-composer";
import { chatApi } from "@/features/chat/api";
vi.mock("@/lib/api/client", () => ({ apiRequest: vi.fn() }));
vi.mock("@/features/chat/api", () => ({ chatApi: { sendAttachment: vi.fn() } }));
const request = vi.mocked(apiRequest);
afterEach(() => { cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals(); });
class Upload {
  static fail = false; static sends: Upload[] = []; status = 200; timeout = 0; upload = { onprogress: null as ((event: { lengthComputable: boolean; loaded: number; total: number }) => void) | null }; headers: Record<string,string> = {}; url = "";
  onload: (() => void) | null = null; onerror: (() => void) | null = null; ontimeout: (() => void) | null = null; onabort: (() => void) | null = null;
  open(method: string, url: string) { expect(method).toBe("PUT"); this.url = url; }
  setRequestHeader(key: string,value: string) { this.headers[key] = value; }
  getResponseHeader() { return '"etag"'; }
  send() { Upload.sends.push(this); this.upload.onprogress?.({ lengthComputable: true, loaded: 1,total: 1 }); queueMicrotask(() => { if (Upload.fail) this.onerror?.(); else this.onload?.(); }); }
  abort() { this.onabort?.(); }
}
const file = () => new File([new Uint8Array([0x1a,0x45,0xdf,0xa3,0,0,0,0])], "note.webm", { type: "audio/webm" });
function signing() { request.mockResolvedValueOnce({ media_id: "media-1", upload_strategy: "SIMPLE", upload_url: "https://private.example/object?signature=secret", required_headers: { "Content-Type": "audio/webm" } }).mockResolvedValueOnce({ status: "READY" }); }
describe("attachment contract", () => {
  it("validates MIME, empty files, size and single-selection", () => {
    expect(validateAttachment([file()])).toBe("audio");
    expect(() => validateAttachment([])).toThrow("one attachment");
    expect(() => validateAttachment([file(),file()])).toThrow("one attachment");
    expect(() => validateAttachment([new File([],"x.pdf",{type:"application/pdf"})])).toThrow("empty");
    expect(() => validateAttachment([new File(["x"],"x.exe",{type:"application/octet-stream"})])).toThrow("supported");
    const large = new File(["x"],"x.png",{type:"image/png"}); Object.defineProperty(large,"size",{value:11*1024**2}); expect(() => validateAttachment([large])).toThrow("size limit");
  });
  it("uploads bytes directly without bearer tokens then finalizes", async () => {
    Upload.fail = false; Upload.sends = []; vi.stubGlobal("XMLHttpRequest", Upload); signing(); const progress = vi.fn();
    const result = await uploadAttachment(file(),"conversation", "token", new AbortController().signal, progress);
    expect(result.media_id).toBe("media-1"); expect(progress).toHaveBeenCalledWith(100); expect(Upload.sends[0].headers).toEqual({"Content-Type":"audio/webm"});
    expect(request).toHaveBeenLastCalledWith("/api/v1/media/media-1/complete",expect.objectContaining({method:"POST"}),"token");
  });
  it("failed upload never finalizes and retry obtains fresh authorization", async () => {
    Upload.fail = true; vi.stubGlobal("XMLHttpRequest", Upload); request.mockResolvedValueOnce({ media_id:"failed", upload_strategy:"SIMPLE", upload_url:"https://private.example/failed" });
    await expect(uploadAttachment(file(),"c","token",new AbortController().signal,vi.fn())).rejects.toThrow("connection"); expect(request).toHaveBeenCalledTimes(1);
    Upload.fail = false; signing(); await expect(uploadAttachment(file(),"c","token",new AbortController().signal,vi.fn())).resolves.toMatchObject({media_id:"media-1"});
  });
  it("cancelled upload rejects without success", async () => { vi.stubGlobal("XMLHttpRequest",Upload); const abort = new AbortController(); abort.abort(); await expect(putFile("https://private.example/file",file(),{},abort.signal,vi.fn())).rejects.toMatchObject({name:"AbortError"}); });
});
it.each(["image", "video", "audio", "document"] as const)("renders real %s attachment through signed download", async media_type => {
  request.mockResolvedValueOnce({download_url:"https://private.example/download"}); const {container} = render(<MediaContent attachment={{media_id:"m",media_type,filename:"file",mime_type:"audio/webm",size_bytes:100}} token="token"/>);
  await screen.findByText("Download attachment"); expect(request).toHaveBeenCalledWith("/api/v1/media/m/download",{},"token");
  if(media_type !== "document") expect(container.querySelector(media_type === "image" ? "img" : media_type)).not.toBeNull();
  if(media_type === "image") { fireEvent.click(screen.getByRole("button",{name:"View file"})); expect(screen.getByRole("dialog")).not.toBeNull(); fireEvent.keyDown(screen.getByRole("dialog"),{key:"Escape"}); expect(screen.queryByRole("dialog")).toBeNull(); }
});
it("permission denial is safe and never uploads", async () => { vi.stubGlobal("MediaRecorder",class {static isTypeSupported(){return true;}}); vi.stubGlobal("navigator",{mediaDevices:{getUserMedia:vi.fn().mockRejectedValue(new Error("denied"))}}); render(<VoiceRecorder disabled={false} onRecorded={vi.fn()}/>); fireEvent.click(screen.getByRole("button", { name: "Record voice note" })); await screen.findByRole("alert"); expect(request).not.toHaveBeenCalled(); });
function recordingHarness() {
  const stop = vi.fn(); const media = {getTracks:()=>[{stop}]}; const instances: Recorder[] = [];
  class Recorder { static isTypeSupported(){return true;} state="inactive"; ondataavailable: ((event:{data:Blob})=>void)|null=null; onstop:(()=>void)|null=null; onerror:(()=>void)|null=null; constructor(){instances.push(this);} start(){this.state="recording";} stop(){this.state="inactive"; this.ondataavailable?.({data:new Blob([new Uint8Array([0x1a,0x45,0xdf,0xa3,0,0,0,0])])});this.onstop?.();} }
  vi.stubGlobal("MediaRecorder",Recorder); vi.stubGlobal("navigator",{mediaDevices:{getUserMedia:vi.fn().mockResolvedValue(media)}}); return {stop,getRecorder:()=>instances[0]};
}
it("voice recording produces a local preview file only after stop", async () => { const harness=recordingHarness(); const recorded=vi.fn(); render(<VoiceRecorder disabled={false} onRecorded={recorded}/>);fireEvent.click(screen.getByRole("button", { name: "Record voice note" })); await screen.findByRole("button", { name: "Stop recording" }); expect(recorded).not.toHaveBeenCalled();fireEvent.click(screen.getByRole("button", { name: "Stop recording" }));expect(recorded).toHaveBeenCalledWith(expect.objectContaining({type:"audio/webm"}));expect(harness.stop).toHaveBeenCalled();expect(request).not.toHaveBeenCalled(); });
it("unmount stops recorder and tracks without producing a voice note", async () => { const harness=recordingHarness();const recorded=vi.fn();const view=render(<VoiceRecorder disabled={false} onRecorded={recorded}/>);fireEvent.click(screen.getByRole("button", { name: "Record voice note" }));await screen.findByRole("button", { name: "Stop recording" });view.unmount();expect(harness.getRecorder().state).toBe("inactive");expect(harness.stop).toHaveBeenCalled();expect(recorded).not.toHaveBeenCalled(); });
it("attachment message retries reuse ready media and the idempotency key", async () => {
  vi.stubGlobal("XMLHttpRequest",Upload); Upload.fail=false; vi.stubGlobal("URL", class extends URL { static createObjectURL(){return "blob:preview";} static revokeObjectURL(){} }); signing(); const onSent=vi.fn(); vi.mocked(chatApi.sendAttachment).mockRejectedValueOnce(new Error("not ready")).mockResolvedValueOnce({id:"message"} as Awaited<ReturnType<typeof chatApi.sendAttachment>>);
  render(<AttachmentComposer conversationId="c" token="token" onSent={onSent}/>); fireEvent.change(screen.getByLabelText("Choose attachment"),{target:{files:[file()]}});expect(request).not.toHaveBeenCalled();fireEvent.click(screen.getByText("Send attachment"));await screen.findByText("Retry attachment");expect(onSent).not.toHaveBeenCalled();fireEvent.click(screen.getByText("Retry attachment"));await waitFor(()=>expect(onSent).toHaveBeenCalledOnce());expect(request).toHaveBeenCalledTimes(2);const calls=vi.mocked(chatApi.sendAttachment).mock.calls;expect(calls[0]).toEqual(calls[1]);
});

it("corrupt selection is rejected before signing", async () => { await expect(inspectFile(new File(["not an image"], "bad.png", {type:"image/png"}))).rejects.toThrow("corrupt"); expect(request).not.toHaveBeenCalled(); });
it("multipart uploads capture ETags then confirm all parts", async () => { Upload.fail=false; Upload.sends=[];vi.stubGlobal("XMLHttpRequest",Upload);request.mockResolvedValueOnce({media_id:"multi",upload_strategy:"MULTIPART",part_size:4,part_count:2}).mockResolvedValueOnce([{part_number:1,presigned_url:"https://private.example/part1"}]).mockResolvedValueOnce([{part_number:2,presigned_url:"https://private.example/part2"}]).mockResolvedValueOnce({status:"READY"});await uploadAttachment(file(),"c","token",new AbortController().signal,vi.fn());expect(Upload.sends).toHaveLength(2);expect(request).toHaveBeenLastCalledWith("/api/v1/media/multi/multipart/complete",expect.objectContaining({body:JSON.stringify({parts:[{part_number:1,etag:'"etag"'},{part_number:2,etag:'"etag"'}]})}),"token"); });

it("recorded voice previews locally and sends VOICE only after explicit Send", async () => { recordingHarness();vi.stubGlobal("XMLHttpRequest",Upload);Upload.fail=false;vi.stubGlobal("URL",class extends URL {static createObjectURL(){return "blob:voice";}static revokeObjectURL(){}});signing();vi.mocked(chatApi.sendAttachment).mockResolvedValueOnce({id:"voice-message"} as Awaited<ReturnType<typeof chatApi.sendAttachment>>);const sent=vi.fn();const view=render(<AttachmentComposer conversationId="c" token="token" onSent={sent}/>);fireEvent.click(screen.getByRole("button", { name: "Record voice note" }));await screen.findByRole("button", { name: "Stop recording" });fireEvent.click(screen.getByRole("button", { name: "Stop recording" }));await screen.findByRole("region",{name:"Attachment preview"});await waitFor(()=>expect(view.container.querySelector("audio")).not.toBeNull());expect(request).not.toHaveBeenCalled();fireEvent.click(screen.getByText("Send attachment"));await waitFor(()=>expect(sent).toHaveBeenCalledOnce());expect(chatApi.sendAttachment).toHaveBeenCalledWith("c","VOICE","media-1",expect.any(String),"token"); });
it("multipart failure aborts the private upload instead of confirming", async () => { Upload.fail=true;vi.stubGlobal("XMLHttpRequest",Upload);request.mockResolvedValueOnce({media_id:"multi",upload_strategy:"MULTIPART",part_size:4,part_count:2}).mockResolvedValueOnce([{part_number:1,presigned_url:"https://private.example/part1"}]).mockResolvedValueOnce({status:"aborted"});await expect(uploadAttachment(file(),"c","token",new AbortController().signal,vi.fn())).rejects.toThrow("connection");expect(request).toHaveBeenLastCalledWith("/api/v1/media/multi/multipart",{method:"DELETE"},"token");Upload.fail=false; });
