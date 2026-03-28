"use client";

import { useState } from "react";
import useClasses from "@/utils/useClasses";
import { StyledTooltipStyles } from "./StyledTooltipStyles";

interface StyledTooltipProps {
  text: string;
  children: React.ReactNode;
}

export default function StyledTooltip({ text, children }: StyledTooltipProps) {
  const [show, setShow] = useState(false);
  const classes = useClasses(StyledTooltipStyles, { name: "StyledTooltip" });

  return (
    <span
      style={{ position: "relative", display: "inline-block", cursor: "pointer" }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div
          className={classes.tooltip}
          style={{
            position: "absolute",
            bottom: "100%",
            left: "50%",
            transform: "translateX(-50%)",
            marginBottom: "4px",
            whiteSpace: "nowrap",
            zIndex: 10,
          }}
        >
          {text}
        </div>
      )}
    </span>
  );
}
