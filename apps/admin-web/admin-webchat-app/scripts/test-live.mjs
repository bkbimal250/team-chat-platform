import { chromium } from "playwright";
import { readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createSign, randomUUID } from "node:crypto";
const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const root = path.resolve(app, "../../..");
const local = path.join(root, ".local");
const base = process.env.ADMIN_BASE_URL ?? "http://127.0.0.1:3000";
if (!["localhost", "127.0.0.1"].includes(new URL(base).hostname))
  throw new Error("Local admin only");
const fixture = JSON.parse(
  await readFile(path.join(local, "admin-fixtures.json"), "utf8"),
);
const results = {};
let step = "bootstrap";
function check(name, passed) {
  step = name;
  results[name] = passed ? "PASS" : "FAIL";
  console.log(name, results[name]);
  if (!passed) throw new Error("Live check failed");
}
async function api(route, token, method = "GET", body) {
  const response = await fetch(base + "/api/gateway" + route, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return {
    status: response.status,
    body: await response.json().catch(() => null),
  };
}
const directories = await readdir(
  path.join(process.env.LOCALAPPDATA, "ms-playwright"),
);
const cached = directories.find(
  (value) => value.startsWith("chromium-") && !value.includes("headless"),
);
const browser = await chromium.launch(
  cached
    ? {
        executablePath: path.join(
          process.env.LOCALAPPDATA,
          "ms-playwright",
          cached,
          "chrome-win",
          "chrome.exe",
        ),
        headless: true,
      }
    : { channel: "msedge", headless: true },
);
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
try {
  let critical = false;
  page.on("pageerror", () => {
    critical = true;
  });
  const ready = await api("/health/ready");
  check("gateway_bridge_ready", ready.status === 200);
  const denied = await api("/api/v1/members/");
  check("no_token_rejected", denied.status === 401);
  const invalid = await api("/api/v1/members/", "invalid-token");
  check("invalid_token_rejected", invalid.status === 401);
  async function login(phone) {
    step = "login page";
    await page.goto(base + "/login");
    await page.getByRole("textbox", { name: "Phone number" }).fill(phone);
    const request = page.waitForResponse(
      (r) =>
        r.url().includes("/auth/otp/request") &&
        r.request().method() === "POST",
    );
    step = "OTP request UI";
    await page.getByRole("button", { name: "Request code" }).click();
    const response = await request;
    const challenge = await response.json();
    console.log("Local OTP HTTP status", response.status(), "code provided", Boolean(challenge.development_code));
    if (![200, 202].includes(response.status()) || !challenge.development_code)
      throw new Error("Local development OTP required; no provider retry");
    await page
      .getByRole("textbox", { name: "Verification code" })
      .fill(challenge.development_code);
    const verify = page.waitForResponse(
      (r) =>
        r.url().includes("/auth/otp/verify") && r.request().method() === "POST",
    );
    await page.getByRole("button", { name: "Verify and sign in" }).click();
    step = "OTP verify UI";
    const verified = await verify;
    if (verified.status() !== 200) throw new Error("OTP verification failed");
    return verified.json();
  }
  let tokens = await login("+919000000001");
  check("real_otp_login", Boolean(tokens.access_token && tokens.refresh_token));
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  check("verified_admin_dashboard", true);
  const assignments = await api(
    "/api/v1/role-assignments/?member=" + tokens.member_id,
    tokens.access_token,
  );
  const roles = await api("/api/v1/roles/", tokens.access_token);
  check(
    "real_admin_role_assignment",
    assignments.status === 200 &&
      roles.status === 200 &&
      assignments.body.results.some((a) =>
        roles.body.results.some(
          (r) =>
            r.id === a.role && r.permissions.includes("organization.update"),
        ),
      ),
  );
  const claims = JSON.parse(
    Buffer.from(tokens.access_token.split(".")[1], "base64url").toString(),
  );
  claims.exp = Math.floor(Date.now() / 1000) - 60;
  const unsigned =
    tokens.access_token.split(".")[0] +
    "." +
    Buffer.from(JSON.stringify(claims)).toString("base64url");
  const signer = createSign("RSA-SHA256");
  signer.update(unsigned);
  const expired =
    unsigned +
    "." +
    signer.sign(
      await readFile(path.join(local, "jwt-private.pem")),
      "base64url",
    );
  check(
    "expired_token_rejected",
    (await api("/api/v1/members/", expired)).status === 401,
  );
  await page.evaluate(
    (value) =>
      sessionStorage.setItem("globalchat.admin.session", JSON.stringify(value)),
    { ...tokens, access_token: expired },
  );
  const refresh = page.waitForResponse(
    (r) => r.url().includes("/auth/refresh") && r.request().method() === "POST",
  );
  await page.reload();
  check("automatic_refresh", (await refresh).status() === 200);
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  tokens = await page.evaluate(() =>
    JSON.parse(sessionStorage.getItem("globalchat.admin.session")),
  );
  check(
    "refreshed_admin_session",
    Boolean(tokens.access_token && tokens.access_token !== expired),
  );
  for (const resource of [
    "members",
    "branches",
    "teams",
    "invitations",
    "roles",
    "audit-logs",
  ]) {
    const response = await api(
      `/api/v1/${resource}/?page_size=10`,
      tokens.access_token,
    );
    check(
      resource + "_real_api",
      response.status === 200 && Array.isArray(response.body.results),
    );
  }
  const organization = await api(
    "/api/v1/organizations/current/",
    tokens.access_token,
  );
  check(
    "current_organization_api",
    organization.status === 200 &&
      organization.body.id === tokens.organization_id,
  );
  await page.goto(base + "/organizations");
  await page
    .getByText(organization.body.name, { exact: true })
    .first()
    .waitFor();
  check("real_organization_ui", true);
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  const orgPatch = page.waitForResponse(
    (r) =>
      r.url().includes("organizations/current/") &&
      r.request().method() === "PATCH",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  check("organization_update_ui", (await orgPatch).status() === 200);
  await page.goto(base + "/organizations/" + organization.body.id);
  await page.getByRole("button", { name: "Branches", exact: true }).click();
  await page.getByText("Newest first (server ordering)").waitFor();
  check("organization_detail_tabs", true);
  await page.goto(base + "/organizations/" + fixture.foreign_organization_id);
  await page.getByText("Organization unavailable", { exact: true }).waitFor();
  check("wrong_organization_frontend_protected", true);
  check(
    "cross_tenant_branch_rejected",
    (
      await api(
        "/api/v1/branches/" + fixture.foreign_branch_id + "/",
        tokens.access_token,
      )
    ).status === 404,
  );
  check(
    "malformed_resource_id_rejected",
    [400, 404, 422].includes(
      (await api("/api/v1/branches/not-a-uuid/", tokens.access_token)).status,
    ),
  );
  const suffix = randomUUID().slice(0, 8);
  const name = "Local admin branch " + suffix;
  await page.goto(base + "/branches");
  await page.getByRole("button", { name: "Add branch" }).click();
  await page.getByRole("textbox", { name: "Name", exact: true }).fill(name);
  await page
    .getByRole("textbox", { name: "Code", exact: true })
    .fill("LIVE" + suffix);
  await page
    .getByRole("textbox", { name: "Country code", exact: true })
    .fill("IN");
  const create = page.waitForResponse(
    (r) => r.url().includes("/branches/") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  const created = await create;
  const branch = await created.json();
  check("branch_create_ui", created.status() === 201);
  const row = page.getByRole("row").filter({ hasText: name });
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await page
    .getByRole("textbox", { name: "City", exact: true })
    .fill("Local test city");
  const patch = page.waitForResponse(
    (r) => r.url().includes(branch.id) && r.request().method() === "PATCH",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  check("branch_edit_ui", (await patch).status() === 200);
  await row.getByRole("button", { name: "Disable", exact: true }).click();
  check(
    "destructive_confirmation_visible",
    await page.getByRole("dialog", { name: "Confirm change" }).isVisible(),
  );
  const disable = page.waitForResponse(
    (r) =>
      r.url().includes(branch.id + "/lifecycle/") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  check("branch_disable_ui", (await disable).status() === 200);
  await row.getByRole("button", { name: "Activate", exact: true }).click();
  const activate = page.waitForResponse(
    (r) =>
      r.url().includes(branch.id + "/lifecycle/") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  check("branch_activate_ui", (await activate).status() === 200);
  await page.goto(base + "/members");
  await page.getByRole("button", { name: "Add member" }).click();
  await page
    .getByRole("textbox", { name: "Display name" })
    .fill("Unlinked admin test " + suffix);
  const memberPost = page.waitForResponse(
    (r) => r.url().includes("/members/") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  const memberResult = await memberPost;
  check(
    "member_create_unlinked_ui",
    memberResult.status() === 201 &&
      (await memberResult.json()).user_id === null,
  );
  await page.goto(base + "/teams");
  await page.getByRole("button", { name: "Add team" }).click();
  await page
    .getByRole("textbox", { name: "Name", exact: true })
    .fill("Local admin team " + suffix);
  const teamPost = page.waitForResponse(
    (r) => r.url().includes("/teams/") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  check("team_create_ui", (await teamPost).status() === 201);
  await page.goto(base + "/invitations");
  await page.getByRole("button", { name: "Add invitation" }).click();
  await page.getByLabel("Intended role").selectOption({ label: "MEMBER" });
  await page
    .getByLabel("Expires at")
    .fill(new Date(Date.now() + 86400000).toISOString().slice(0, 16));
  const invitePost = page.waitForResponse(
    (r) => r.url().includes("/invitations/") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Save", exact: true }).click();
  const inviteResponse = await invitePost;
  const invitation = await inviteResponse.json();
  check("invitation_create_ui", inviteResponse.status() === 201);
  await page
    .getByRole("row")
    .filter({ hasText: invitation.id })
    .getByRole("button", { name: "Revoke", exact: true })
    .click();
  const revoke = page.waitForResponse(
    (r) =>
      r.url().includes(invitation.id + "/revoke/") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Confirm", exact: true }).click();
  check("invitation_revoke_ui", (await revoke).status() === 200);
  await page.goto(base + "/settings");
  const orgSettings = page.waitForResponse(
    (r) =>
      r.url().includes("organizations/current/settings/") &&
      r.request().method() === "PATCH",
  );
  await page
    .getByRole("button", { name: "Save organization settings" })
    .click();
  check("organization_settings_save_ui", (await orgSettings).status() === 200);
  const preference = page.waitForResponse(
    (r) =>
      r.url().includes("notifications/preferences") &&
      r.request().method() === "PATCH",
  );
  await page
    .getByRole("button", { name: "Save notification preferences" })
    .click();
  check("notification_settings_save_ui", (await preference).status() === 200);
  await page.goto(base + "/devices");
  await page
    .getByRole("heading", { name: "Your devices and sessions" })
    .waitFor();
  check(
    "own_device_api",
    (await api("/api/v1/devices", tokens.access_token)).status === 200,
  );
  check(
    "own_session_api",
    (await api("/api/v1/auth/sessions", tokens.access_token)).status === 200,
  );
  await page.goto(base + "/notifications");
  await page.getByRole("heading", { name: "Your notifications" }).waitFor();
  check(
    "own_notification_api",
    (await api("/api/v1/notifications", tokens.access_token)).status === 200,
  );
  await page.goto(base + "/dashboard");
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  await page.screenshot({
    path: path.join(local, "admin-dashboard.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Local Alice", exact: true }).click();
  const logout = page.waitForResponse(
    (r) => r.url().includes("/auth/logout") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  check("logout_ui", (await logout).status() === 200);
  await page.waitForURL("**/login");
  check(
    "logout_route_protection",
    await page
      .getByRole("heading", { name: "Sign in to your workspace" })
      .isVisible(),
  );
  const normal = await login("+919000000002");
  await page
    .getByRole("heading", { name: "Organization admin access required" })
    .waitFor();
  check("normal_user_admin_rejected", true);
  check(
    "normal_user_mutation_rejected",
    (
      await api("/api/v1/branches/", normal.access_token, "POST", {
        name: "Forbidden",
        code: "FORBIDDEN",
        country: "IN",
      })
    ).status === 403,
  );
  check(
    "other_users_device_rejected",
    (await api("/api/v1/devices/" + tokens.device_id, normal.access_token))
      .status === 404,
  );
  await api("/api/v1/auth/logout", normal.access_token, "POST", {});
  check("no_browser_exceptions", !critical);
} catch (error) {
  console.log("STOPPED AT", step, "CATEGORY", error?.name ?? "Error");
  process.exitCode = 1;
} finally {
  await writeFile(
    path.join(local, "admin-live-results.json"),
    JSON.stringify(results, null, 2),
  );
  await browser.close();
  console.log(
    "Live assertions",
    Object.values(results).filter((x) => x === "PASS").length,
    "passed",
    Object.values(results).filter((x) => x === "FAIL").length,
    "failed",
  );
}
