import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false, // Disable React Strict Mode
  output: 'export', // Enable static HTML export for Tauri
  images: {
    unoptimized: true, // Required for static export
  },
  // Disable server-side features that don't work with static export
  distDir: 'out',
};

export default nextConfig;
