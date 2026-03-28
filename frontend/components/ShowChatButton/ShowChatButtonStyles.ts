import { Theme } from "@/utils/theme";

const showChatButtonStyles = (theme: Theme) => ({
  wrapper: {
    position: "absolute" as const,
    right: "0",
    top: "50%",
    transform: "translateY(-50%)",
    zIndex: 10,
    backgroundColor: theme.colors.surface.containerLowest,
    border: "none",
    borderRadius: "12px 0 0 12px",
    padding: "14px 8px",
    cursor: "pointer",
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.xs,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    writingMode: "vertical-rl" as const,
    textOrientation: "mixed" as const,
    letterSpacing: "1px",
    userSelect: "none" as const,
    transition: "all 0.15s ease",
    boxShadow: theme.shadows.md,
    textTransform: "uppercase" as const,
    "&:hover": {
      backgroundColor: theme.colors.surface.containerLow,
      color: theme.colors.text.primary,
    },
  },
  wrapperClosed: {
    color: "#10B981",
    animation: "pulseGlow 2s ease-in-out infinite",
  },
  wrapperOpen: {
    color: "#EF4444",
    animation: "pulseWarn 2s ease-in-out infinite",
  },
});

export default showChatButtonStyles;
