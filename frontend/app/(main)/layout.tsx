"use client";

import Header from "@/components/generic_components/Header/Header";
import Sidebar from "@/components/generic_components/Sidebar/Sidebar";
import theme from "@/utils/theme";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <Sidebar />
      <div style={{ display: "flex", flexDirection: "column", flex: 1, overflow: "hidden" }}>
        <Header pageName="Dashboard" />
        <div style={{ flex: 1, overflow: "auto", backgroundColor: theme.layout.pageColor }}>{children}</div>
      </div>
    </div>
  );
}
