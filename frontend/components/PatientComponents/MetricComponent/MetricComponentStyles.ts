import { Theme } from "@/utils/theme";

export const MetricComponentStyles = (theme: Theme) => ({
  metricBox: {
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
  },
  metricLabel: {
    fontSize: "0.65rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    margin: "0 0 2px",
    textAlign: "center" as const,
  },
  metricValue: {
    fontSize: "1.25rem",
    fontWeight: theme.typography.fontWeight.bold,
    fontFamily: theme.typography.fontFamilyHeading,
    color: theme.colors.text.primary,
    margin: 0,
    lineHeight: 1.2,
    textAlign: "center" as const,
  },
  metricUnit: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.regular,
    color: theme.colors.text.secondary,
    marginLeft: "3px",
  },
});
