import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    unoptimized: true, // Required for static Next.js exports
  }
};

export default nextConfig;
