import { Theme } from "@/utils/theme";

export const KpiPrimaryRowStyles = (theme: Theme) => ({
  row: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: theme.spacing.md,
    flexShrink: 0,
    "@media (max-width: 1100px)": {
      gridTemplateColumns: "repeat(2, 1fr)",
    },
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
  sub: {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.primary.main,
    fontWeight: theme.typography.fontWeight.medium,
    margin: 0,
  },
});
