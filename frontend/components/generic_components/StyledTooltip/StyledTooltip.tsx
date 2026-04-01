"use client";

import MuiTooltip from "@mui/material/Tooltip";
import theme from "@/utils/theme";

interface StyledTooltipProps {
  text: React.ReactNode;
  children: React.ReactElement;
  placement?: "top" | "bottom" | "left" | "right";
  disabled?: boolean;
}

export default function StyledTooltip({
  text,
  children,
  placement = "top",
  disabled = false,
}: StyledTooltipProps) {
  return (
    <MuiTooltip
      title={disabled ? "" : text}
      placement={placement}
      arrow
      slotProps={{
        tooltip: {
          sx: {
            backgroundColor: "#1e2530",
            color: "#f1f5f9",
            boxShadow: theme.shadows.lg,
            fontSize: theme.typography.fontSize.sm,
            fontFamily: theme.typography.fontFamily,
            borderRadius: theme.borderRadius.sm,
            padding: "6px 10px",
            maxWidth: 320,
          },
        },
        arrow: {
          sx: { color: "#1e2530" },
        },
      }}
    >
      {children}
    </MuiTooltip>
  );
}
