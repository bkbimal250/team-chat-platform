import { chromium } from "playwright";
import { readFile, writeFile, readdir } from "node:fs/promises";
import path from "node:path";
import { randomUUID, randomInt } from "node:crypto";
const base = "http://127.0.0.1:3000",
  local = path.resolve("../../../.local"),
  results = {};
let stage = "startup";
function check(name, ok) {
  stage = name;
  results[name] = ok ? "PASS" : "FAIL";
  console.log(name, results[name]);
  if (!ok) throw Error("Live check failed");
}
async function api(route, token, method = "GET", body) {
  const r = await fetch(base + "/api/gateway" + route, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  return { status: r.status, body: await r.json().catch(() => null) };
}
const cache = await readdir(
  path.join(process.env.LOCALAPPDATA, "ms-playwright"),
);
const cached = cache.find(
  (x) => x.startsWith("chromium-") && !x.includes("headless"),
);
const browser = await chromium.launch({
  executablePath: path.join(
    process.env.LOCALAPPDATA,
    "ms-playwright",
    cached,
    "chrome-win/chrome.exe",
  ),
  headless: true,
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
let errors = false;
page.on("pageerror", () => {
  errors = true;
});
const company = "Development Registration " + randomUUID().slice(0, 8),
  owner = "Development Company Owner",
  phone = "+9197" + String(randomInt(10000000, 99999999)),
  email = randomUUID() + "@example.com";
try {
  await page.goto(base + "/register");
  for (const [name, value] of [
    ["Company Name", company],
    ["Owner Name", owner],
    ["Email", email],
    ["Phone Number", phone],
  ])
    await page.getByRole("textbox", { name }).fill(value);
  const start = page.waitForResponse((r) =>
    r.url().endsWith("/registration/company/start"),
  );
  await page.getByRole("button", { name: "Request registration code" }).click();
  const started = await start,
    challenge = await started.json();
  check("registration_start", started.status() === 202);
  check("development_otp", Boolean(challenge.development_code));
  check(
    "opaque_challenge",
    Boolean(challenge.registration_id) && !challenge.organization_id,
  );
  await page
    .getByRole("textbox", { name: "Verification code" })
    .fill(challenge.development_code);
  const verify = page.waitForResponse((r) =>
    r.url().endsWith("/registration/company/verify"),
  );
  await page.getByRole("button", { name: "Verify and create company" }).click();
  const response = await verify,
    tokens = await response.json();
  check(
    "verified_session_issued",
    response.status() === 200 &&
      Boolean(tokens.access_token) &&
      Boolean(tokens.refresh_token),
  );
  await page.waitForURL("**/dashboard");
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  check("admin_owner_dashboard", true);
  const org = await api("/api/v1/organizations/current/", tokens.access_token);
  check(
    "organization_created",
    org.status === 200 && org.body.name === company,
  );
  const profile = await api("/api/v1/users/me", tokens.access_token);
  check(
    "owner_profile",
    profile.status === 200 && profile.body.display_name === owner,
  );
  const members = await api("/api/v1/members/", tokens.access_token);
  check(
    "owner_membership",
    members.status === 200 &&
      members.body.results.some(
        (m) => m.id === tokens.member_id && m.display_name === owner,
      ),
  );
  const roles = await api("/api/v1/roles/", tokens.access_token),
    assignments = await api(
      "/api/v1/role-assignments/?member=" + tokens.member_id,
      tokens.access_token,
    ),
    ownerRole = roles.body.results.find((r) => r.kind === "OWNER");
  check(
    "owner_role",
    Boolean(ownerRole) &&
      assignments.body.results.some((r) => r.role === ownerRole.id),
  );
  check("owner_permissions", ownerRole.permissions.includes("member.create"));
  const body = {
    registration_id: challenge.registration_id,
    otp: challenge.development_code,
    device: {
      installation_id: randomUUID(),
      platform: "WEB",
      device_name: "Development browser",
    },
  };
  check(
    "replay_rejected",
    (await api("/api/v1/auth/registration/company/verify", null, "POST", body))
      .status === 409,
  );
  check(
    "duplicate_rejected",
    (
      await api("/api/v1/auth/registration/company/start", null, "POST", {
        company_name: company,
        owner_name: owner,
        email,
        phone,
      })
    ).status === 409,
  );
  const fixture = JSON.parse(
    await readFile(path.join(local, "admin-fixtures.json"), "utf8"),
  );
  check(
    "cross_tenant_rejected",
    (
      await api(
        "/api/v1/branches/" + fixture.foreign_branch_id + "/",
        tokens.access_token,
      )
    ).status === 404,
  );
  await page.getByRole("button", { name: owner, exact: true }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.waitForURL("**/login");
  check("logout", true);
  await page.getByRole("textbox", { name: "Phone number" }).fill(phone);
  const requested = page.waitForResponse((r) =>
    r.url().includes("/auth/otp/request"),
  );
  await page.getByRole("button", { name: "Request code" }).click();
  const req = await requested,
    loginChallenge = await req.json();
  check("returning_otp", req.status() === 202);
  await page
    .getByRole("textbox", { name: "Verification code" })
    .fill(loginChallenge.development_code);
  const logged = page.waitForResponse((r) =>
    r.url().includes("/auth/otp/verify"),
  );
  await page.getByRole("button", { name: "Verify and sign in" }).click();
  const login = await logged,
    returned = await login.json();
  check("returning_login", login.status() === 200);
  await page.waitForURL("**/dashboard");
  await page.getByRole("heading", { name: "Dashboard", exact: true }).waitFor();
  check(
    "same_organization",
    returned.organization_id === tokens.organization_id,
  );
  check("same_membership", returned.member_id === tokens.member_id);
  check(
    "same_profile",
    (await api("/api/v1/users/me", returned.access_token)).body.user_id ===
      profile.body.user_id,
  );
  check("no_browser_errors", !errors);
  await writeFile(
    path.join(local, "company-registration-check.json"),
    JSON.stringify({
      registration_id: challenge.registration_id,
      organization_id: tokens.organization_id,
      member_id: tokens.member_id,
    }),
  );
  await page.screenshot({
    path: path.join(local, "company-registration-dashboard.png"),
    fullPage: true,
  });
} catch {
  console.log("Stopped at", stage);
  process.exitCode = 1;
} finally {
  await writeFile(
    path.join(local, "company-registration-results.json"),
    JSON.stringify(results, null, 2),
  );
  await browser.close();
  console.log(
    "Assertions",
    Object.values(results).filter((x) => x === "PASS").length,
    "passed",
    Object.values(results).filter((x) => x === "FAIL").length,
    "failed",
  );
}
