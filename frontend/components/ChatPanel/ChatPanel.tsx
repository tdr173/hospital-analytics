"use client";

import { useState, useRef, useEffect } from "react";
import useClasses from "@/utils/useClasses";
import chatPanelStyles from "./ChatPanelStyles";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: Date;
}

export default function ChatPanel() {
  const classes = useClasses(chatPanelStyles, { name: "ChatPanel" });
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = "38px";
    }

    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "ai",
        content:
          "This is a placeholder response. Connect the backend to enable real AI responses.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1200);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const textarea = e.target;
    textarea.style.height = "38px";
    textarea.style.height = Math.min(textarea.scrollHeight, 100) + "px";
  };

  return (
    <div className={classes.container}>
      <div className={classes.header}>
        <div className={classes.headerTitle}>
          <span className={classes.headerDot} />
          AI Assistant
        </div>
      </div>

      <div className={classes.messages}>
        {messages.length === 0 && !isLoading && (
          <div className={classes.emptyState}>
            <div className={classes.emptyIcon}>AI</div>
            <div>Ask me anything about the data.</div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`${classes.messageRow} ${
              msg.role === "user"
                ? classes.messageRowUser
                : classes.messageRowAi
            }`}
          >
            <span className={classes.messageSender}>
              {msg.role === "user" ? "You" : "AI"}
            </span>
            <div
              className={
                msg.role === "user"
                  ? classes.messageBubbleUser
                  : classes.messageBubbleAi
              }
            >
              {msg.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className={`${classes.messageRow} ${classes.messageRowAi}`}>
            <span className={classes.messageSender}>AI</span>
            <div className={classes.typingIndicator}>
              <span
                className={classes.typingDot}
                style={{ animationDelay: "0s" }}
              />
              <span
                className={classes.typingDot}
                style={{ animationDelay: "0.2s" }}
              />
              <span
                className={classes.typingDot}
                style={{ animationDelay: "0.4s" }}
              />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className={classes.inputArea}>
        <textarea
          ref={textareaRef}
          className={classes.input}
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the data..."
          rows={1}
        />
        <button
          className={
            !input.trim() || isLoading
              ? classes.sendButtonDisabled
              : classes.sendButton
          }
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
        >
          Send
        </button>
      </div>
    </div>
  );
}
