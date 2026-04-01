"use client";

import { useRef, useState } from "react";
import StyledTooltip from "@/components/generic_components/StyledTooltip/StyledTooltip";

interface TruncatedTextProps {
  text: string;
}

export default function TruncatedText({ text }: TruncatedTextProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [overflowing, setOverflowing] = useState(false);

  const checkOverflow = () => {
    if (ref.current) {
      setOverflowing(ref.current.scrollWidth > ref.current.clientWidth);
    }
  };

  return (
    <StyledTooltip text={text} disabled={!overflowing}>
      <span
        ref={ref}
        onMouseEnter={checkOverflow}
        style={{
          display: "block",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {text}
      </span>
    </StyledTooltip>
  );
}
