import { Theme } from "@/utils/theme";

export const TopConditionsBarStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    height: "100%",
    display: "flex",
    flexDirection: "column" as const,
  },
  title: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.07em",
    margin: `0 0 ${theme.spacing.md} 0`,
  },
  chartWrapper: {
    width: "100%",
  },
  empty: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    width: "100%",
    minHeight: 220,
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
  },
  tooltip: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.8rem",
    borderRadius: theme.borderRadius.md,
    border: `1px solid ${theme.colors.border.main}`,
    boxShadow: theme.shadows.md,
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    backgroundColor: theme.colors.surface.containerLowest,
    color: theme.colors.text.primary,
  },
  tooltipLabel: {
    fontWeight: theme.typography.fontWeight.semibold,
    marginBottom: "2px",
  },
});
