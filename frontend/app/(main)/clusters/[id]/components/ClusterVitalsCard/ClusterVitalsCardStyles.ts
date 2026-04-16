import { Theme } from "@/utils/theme";

export const ClusterVitalsCardStyles = (theme: Theme) => ({
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
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: theme.spacing.md,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "repeat(2, 1fr)",
    },
  },
  statBox: {
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    padding: `${theme.spacing.md} ${theme.spacing.md}`,
  },
  statLabel: {
    fontSize: "0.65rem",
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    marginBottom: "4px",
  },
  statValue: {
    fontSize: "1.5rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
    lineHeight: 1.1,
  },
  statUnit: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.regular,
    color: theme.colors.text.secondary,
    marginLeft: "4px",
  },
});
