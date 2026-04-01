import { Theme } from "@/utils/theme";

export const ClusterFeatureChartStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
  },
  title: {
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.md,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    margin: "0 0 8px 0",
  },
  tooltipBox: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.md,
    boxShadow: theme.shadows.lg,
    padding: "8px 12px",
    fontFamily: theme.typography.fontFamily,
    fontSize: "13px",
    color: theme.colors.text.primary,
    maxWidth: "220px",
  },
  tooltipLineFirst: {
    fontWeight: theme.typography.fontWeight.semibold,
    marginBottom: "4px",
  },
  tooltipLineRest: {
    fontWeight: theme.typography.fontWeight.regular,
    marginBottom: "2px",
  },
});
