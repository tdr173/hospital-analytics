import { Theme } from "@/utils/theme";

export const PieChartStyles = (theme: Theme) => ({
  container: {
    backgroundColor: theme.colors.surface.containerLowest,
    border: "none",
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
  },
  title: {
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.md,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing.sm,
    marginTop: 0,
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
  },
});
