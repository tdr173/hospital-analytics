"use client";

import { useState, useRef, useEffect } from "react";
import useClasses from "@/utils/useClasses";
import chatPanelStyles from "./ChatPanelStyles";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatch, RootState } from "@/store";
import { addQuestion } from "@/store/slices/statistics/sql-agent-slice";
import { getSqlAgentResponse } from "@/store/slices/statistics/thunks";

export default function ChatPanel() {
  const classes = useClasses(chatPanelStyles, { name: "ChatPanel" });
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { questions, results, loading } = useSelector(
    (state: RootState) => state.sqlAgent,
  );
  const dispatch = useDispatch<AppDispatch>();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [questions, results, loading]);

  const buildHistory = () => {
    const history: { role: string; content: string }[] = [];
    const start = Math.max(0, questions.length - 3);
    for (let i = start; i < questions.length; i++) {
      history.push({ role: "user", content: questions[i] });
      if (results[i] !== undefined) {
        history.push({ role: "ai", content: results[i] });
      }
    }
    return history;
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const history = buildHistory();
    dispatch(addQuestion(trimmed));
    setInput("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "38px";
    }

    dispatch(getSqlAgentResponse({ question: trimmed, history }));
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

  const isEmpty = questions.length === 0;

  return (
    <div className={classes.container}>
      <div className={classes.header}>
        <div className={classes.headerTitle}>
          <span className={classes.headerDot} />
          AI Assistant
        </div>
      </div>

      <div className={classes.messages}>
        {isEmpty && !loading && (
          <div className={classes.emptyState}>
            <div className={classes.emptyIcon}>AI</div>
            <div>Ask me anything about the data.</div>
          </div>
        )}

        {questions.map((question, index) => (
          <div key={index}>
            <div
              className={`${classes.messageRow} ${classes.messageRowUser}`}
            >
              <span className={classes.messageSender}>You</span>
              <div className={classes.messageBubbleUser}>{question}</div>
            </div>

            {results[index] !== undefined && (
              <div
                className={`${classes.messageRow} ${classes.messageRowAi}`}
              >
                <span className={classes.messageSender}>AI</span>
                <div className={classes.messageBubbleAi}>
                  {results[index]}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
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
            !input.trim() || loading
              ? classes.sendButtonDisabled
              : classes.sendButton
          }
          onClick={handleSend}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  );
}
