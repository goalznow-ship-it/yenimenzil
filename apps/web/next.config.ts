import type { NextConfig } from "next";

const s3PublicUrl = process.env.NEXT_PUBLIC_S3_PUBLIC_URL;
const s3Hostname = s3PublicUrl ? new URL(s3PublicUrl).hostname : undefined;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com"
      },
      ...(s3Hostname
        ? [{ protocol: "https" as const, hostname: s3Hostname }]
        : []),
      { protocol: "http", hostname: "localhost" },
      { protocol: "http", hostname: "minio" },
      { protocol: "http", hostname: "127.0.0.1" }
    ]
  }
};

export default nextConfig;
