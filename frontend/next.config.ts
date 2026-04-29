import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  transpilePackages: ["@mui/icons-material", "@mui/material", "@mui/system"],
  turbopack: {
    root: ".",
  },
};

export default nextConfig;
