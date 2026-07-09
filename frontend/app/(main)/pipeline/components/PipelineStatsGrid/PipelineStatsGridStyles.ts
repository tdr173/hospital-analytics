import { Theme } from "@/utils/theme";

export const PipelineStatsGridStyles = (theme: Theme) => ({
  wrapper: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
  },
  section: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  sectionTitle: {
    fontSize: "0.72rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: theme.spacing.md,
  },
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.xs,
    borderTop: `3px solid ${theme.colors.primary.main}`,
  },
  iconRow: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.xs,
  },
  label: {
    fontSize: "0.68rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.07em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  value: {
    fontSize: "1.8rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
    margin: 0,
    lineHeight: 1.1,
  },
});
