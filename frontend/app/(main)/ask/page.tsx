"use client";

import ChatPanel from "@/components/ChatPanel/ChatPanel";

export default function AskPage() {
  return (
    <div
      style={{
        height: "100%",
        width: "100%",
        display: "flex",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "900px",
          height: "100%",
          border: "1px solid #E5E7EB",
          borderRadius: "12px",
          overflow: "hidden",
          backgroundColor: "#ffffff",
        }}
      >
        <ChatPanel />
      </div>
    </div>
  );
}
