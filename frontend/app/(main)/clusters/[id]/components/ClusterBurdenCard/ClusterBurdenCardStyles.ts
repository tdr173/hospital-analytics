import { Theme } from "@/utils/theme";

export const ClusterBurdenCardStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.md,
    padding: `${theme.spacing.lg} ${theme.spacing.xl}`,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.1em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  twoCol: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.xl,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "1fr",
    },
  },
  statsList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.sm,
  },
  statRow: {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
  },
  statLabel: {
    fontSize: "0.75rem",
    color: theme.colors.text.secondary,
    fontWeight: theme.typography.fontWeight.semibold,
  },
  statValue: {
    fontSize: "1rem",
    fontWeight: theme.typography.fontWeight.bold,
    fontFamily: theme.typography.fontFamilyHeading,
    color: theme.colors.text.primary,
  },
  rightColumn: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
  },
  severityBlock: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "flex-end",
    gap: "4px",
  },
  severityValue: {
    fontSize: "2.5rem",
    fontWeight: theme.typography.fontWeight.bold,
    fontFamily: theme.typography.fontFamilyHeading,
    color: theme.colors.text.primary,
    lineHeight: 1,
  },
  severityCaption: {
    fontSize: "0.7rem",
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    fontWeight: theme.typography.fontWeight.semibold,
  },
  legendRow: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: theme.spacing.md,
    fontSize: "0.75rem",
    color: theme.colors.text.secondary,
  },
  legendItem: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
  },
  legendDot: {
    width: "10px",
    height: "10px",
    borderRadius: "2px",
  },
  chartWrapper: {
    width: "100%",
    height: 60,
  },
});
