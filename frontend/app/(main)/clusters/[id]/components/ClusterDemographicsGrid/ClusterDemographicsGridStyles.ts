import { Theme } from "@/utils/theme";

export const ClusterDemographicsGridStyles = (theme: Theme) => ({
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
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.lg,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "1fr",
    },
  },
});
