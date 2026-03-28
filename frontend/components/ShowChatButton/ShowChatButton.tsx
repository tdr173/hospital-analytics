"use client";

import useClasses from "@/utils/useClasses";
import showChatButtonStyles from "./ShowChatButtonStyles";

interface ShowChatButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export default function ShowChatButton({
  isOpen,
  onClick,
}: ShowChatButtonProps) {
  const classes = useClasses(showChatButtonStyles, {
    name: "ShowChatButtonStyles",
  });

  return (
    <div
      className={`${classes.wrapper} ${isOpen ? classes.wrapperOpen : classes.wrapperClosed}`}
      onClick={onClick}
    >
      {isOpen ? "CLOSE AI CHAT" : "OPEN AI CHAT"}
    </div>
  );
}
