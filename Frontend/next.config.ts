import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false, // Disable React Strict Mode
  // Use default server build to support API routes
  output: 'standalone',
  images: {
    unoptimized: true, // Required for static export
  },
  // Disable server-side features that don't work with static export
  // Use default .next directory
};

export default nextConfig;
