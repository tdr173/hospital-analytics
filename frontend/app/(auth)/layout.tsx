"use client";

import AddIcon from "@mui/icons-material/Add";
import theme from "@/utils/theme";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: theme.colors.surface.base,
        position: "relative",
      }}
    >
      <div
        style={{
          height: "70px",
          width: theme.layout.sidebarWidth,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "0 14px",
          gap: "4px",
          position: "absolute",
        }}
      >
        <AddIcon
          sx={{
            color: "#191c1e",
            fontSize: "32px",
            stroke: "#191c1e",
            strokeWidth: 2,
          }}
        />
        <span
          style={{
            fontSize: "24px",
            fontWeight: 700,
            color: "#191c1e",
            lineHeight: 1.2,
            fontFamily: '"Inter", sans-serif',
            letterSpacing: "-0.02em",
          }}
        >
          HospitAI
        </span>
      </div>
      <div
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {children}
      </div>
    </div>
  );
}
