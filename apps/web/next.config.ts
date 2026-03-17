import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    // INTERNAL_API_URL is a server-side env var set in Railway (no NEXT_PUBLIC_ prefix).
    // Falls back to localhost for local development.
    const apiUrl =
      process.env.INTERNAL_API_URL ?? "http://localhost:8001";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
