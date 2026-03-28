"use client";

import Header from "@/components/generic_components/Header/Header";
import Sidebar from "@/components/generic_components/Sidebar/Sidebar";
import ChatPanel from "@/components/ChatPanel/ChatPanel";
import ShowChatButton from "@/components/ShowChatButton/ShowChatButton";
import theme from "@/utils/theme";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/store";
import { toggleChat } from "@/store/slices/ui-slice";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const chatOpen = useSelector((state: RootState) => state.ui.chatOpen);
  const dispatch = useDispatch();

  return (
    <div style={{ display: "flex", height: "100vh", backgroundColor: theme.layout.pageColor }}>
      <Sidebar />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          flex: 1,
          overflow: "hidden",
          position: "relative",
          marginLeft: theme.layout.sidebarWidth,
        }}
      >
        <Header />
        <div style={{ flex: 1, overflow: "auto", backgroundColor: theme.layout.pageColor }}>{children}</div>
        <ShowChatButton isOpen={chatOpen} onClick={() => dispatch(toggleChat())} />
      </div>
      {chatOpen && (
        <div
          style={{
            width: "25%",
            minWidth: "300px",
            height: "100vh",
            flexShrink: 0,
            borderLeft: `1px solid ${theme.colors.border.light}`,
          }}
        >
          <ChatPanel />
        </div>
      )}
    </div>
  );
}
