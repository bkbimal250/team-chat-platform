export function deviceInput() {
  let id = localStorage.getItem("globalchat.installation");
  if (!id) {
    id = `web-${crypto.randomUUID()}`;
    localStorage.setItem("globalchat.installation", id);
  }
  return {
    installation_id: id,
    platform: "WEB",
    device_name: "GlobalChat Web",
    app_version: "1.0.0",
  };
}
