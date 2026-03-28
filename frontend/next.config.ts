import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@mui/icons-material", "@mui/material", "@mui/system"],
  turbopack: {
    root: ".",
  },
};

export default nextConfig;
