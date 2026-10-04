import { serviceConfig } from "@/lib/api/config";
async function proxy(request: Request) {
  const base = serviceConfig.organization;
  if (!base)
    return Response.json(
      { message: "Gateway URL is not configured." },
      { status: 503 },
    );
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api\/gateway/, "");
  if (!path.startsWith("/api/v1/") && !/^\/health\/(live|ready)$/.test(path))
    return Response.json({ message: "Route unavailable." }, { status: 404 });
  const headers = new Headers();
  for (const name of ["authorization", "content-type"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const response = await fetch(
      `${base.replace(/\/$/, "")}${path}${url.search}`,
      {
        method: request.method,
        headers,
        body: ["GET", "HEAD"].includes(request.method)
          ? undefined
          : await request.text(),
        redirect: "manual",
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
      },
    );
    if (response.status >= 300 && response.status < 400)
      return Response.json(
        { message: "Unexpected upstream redirect." },
        { status: 502 },
      );
    return new Response(
      response.status === 204 ? null : await response.text(),
      {
        status: response.status,
        headers: {
          "Content-Type":
            response.headers.get("content-type") ?? "application/json",
          "Cache-Control": "no-store",
        },
      },
    );
  } catch {
    return Response.json(
      { message: "Gateway is unavailable." },
      { status: 502 },
    );
  }
}
export {
  proxy as GET,
  proxy as POST,
  proxy as PATCH,
  proxy as PUT,
  proxy as DELETE,
};
