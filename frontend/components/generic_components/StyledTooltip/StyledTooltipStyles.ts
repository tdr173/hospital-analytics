import { Theme } from "@/utils/theme";

export const StyledTooltipStyles = (theme: Theme) => ({
  wrapper: {
    position: "relative" as const,
    display: "inline-block",
    cursor: "pointer",
  },
  tooltip: {
    backgroundColor: theme.colors.surface.containerLowest,
    border: "none",
    borderRadius: theme.borderRadius.md,
    boxShadow: theme.shadows.xl,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    maxWidth: "300px",
    wordWrap: "break-word" as const,
    position: "absolute" as const,
    bottom: "100%",
    left: "50%",
    transform: "translateX(-50%)",
    marginBottom: "4px",
    whiteSpace: "nowrap" as const,
    zIndex: 10,
  },
});
