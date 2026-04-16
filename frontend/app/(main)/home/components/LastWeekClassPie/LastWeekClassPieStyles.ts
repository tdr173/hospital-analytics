import { Theme } from "@/utils/theme";

export const LastWeekClassPieStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    justifyContent: "flex-start",
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
    minHeight: 220,
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
  },
});
