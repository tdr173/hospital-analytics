import { Theme } from "@/utils/theme";

export const StyledTooltipStyles = (theme: Theme) => ({
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
  },
});
