import { Theme } from "@/utils/theme";

export const StackedBarChartComponentStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
    height: "100%",
    boxSizing: "border-box" as const,
    display: "flex",
    flexDirection: "column" as const,
  },
  title: {
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.md,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    margin: "0 0 8px 0",
  },
});
