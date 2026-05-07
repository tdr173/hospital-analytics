"use client";

import { Suspense } from "react";
import Header from "@/components/generic_components/Header/Header";
import Sidebar from "@/components/generic_components/Sidebar/Sidebar";
import ChatPanel from "@/components/ChatPanel/ChatPanel";
import ShowChatButton from "@/components/ShowChatButton/ShowChatButton";
import RoleGuard from "@/components/RoleGuard/RoleGuard";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/store";
import { toggleChat } from "@/store/slices/ui-slice";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import useClasses from "@/utils/useClasses";
import { MainLayoutStyles } from "./styles";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const chatOpen = useSelector((state: RootState) => state.ui.chatOpen);
  const dispatch = useDispatch();
  const classes = useClasses(MainLayoutStyles, { name: "MainLayout" });

  return (
    <div className={classes.root}>
      <Suspense>
        <RoleGuard>
          <Sidebar />
          <div className={classes.main}>
            <Header />
            <div className={classes.content}>
              {children}
            </div>
            <ShowChatButton
              isOpen={chatOpen}
              onClick={() => dispatch(toggleChat())}
            />
          </div>
        </RoleGuard>
      </Suspense>
      <ToastContainer
        position="bottom-right"
        autoClose={3000}
        hideProgressBar={false}
        theme="light"
      />
      {chatOpen && (
        <div className={classes.chatPanel}>
          <ChatPanel />
        </div>
      )}
    </div>
  );
}
