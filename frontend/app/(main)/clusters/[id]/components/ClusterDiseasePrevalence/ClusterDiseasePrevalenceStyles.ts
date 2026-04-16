import { Theme } from "@/utils/theme";

export const ClusterDiseasePrevalenceStyles = (theme: Theme) => ({
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
  chartWrapper: {
    width: "100%",
    height: 320,
  },
  tooltip: {
    backgroundColor: theme.colors.surface.containerLowest,
    border: `1px solid ${theme.colors.border.main}`,
    borderRadius: theme.borderRadius.md,
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    fontSize: "0.75rem",
    color: theme.colors.text.primary,
  },
  tooltipLabel: {
    fontWeight: theme.typography.fontWeight.semibold,
    marginBottom: "2px",
  },
});
