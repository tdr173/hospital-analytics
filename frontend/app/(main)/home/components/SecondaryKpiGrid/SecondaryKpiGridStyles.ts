import { Theme } from "@/utils/theme";

export const SecondaryKpiGridStyles = (theme: Theme) => ({
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gridTemplateRows: "repeat(2, 1fr)",
    gap: theme.spacing.md,
  },
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.xs,
    borderLeft: `3px solid ${theme.colors.primary.main}`,
  },
  iconRow: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  label: {
    fontSize: "0.6rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  value: {
    fontSize: "1.35rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
    margin: 0,
    lineHeight: 1.1,
  },
});
