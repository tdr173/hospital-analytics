import { Theme } from "@/utils/theme";

export const GenderPieStyles = (theme: Theme) => ({
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
});
