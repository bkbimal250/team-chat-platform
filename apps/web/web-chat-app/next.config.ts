import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Preserve the exact Django resource paths forwarded through the Gateway.
  skipTrailingSlashRedirect: true,
};

export default nextConfig;
