import { Theme } from "@/utils/theme";

export const SequencesPageStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    fontFamily: theme.typography.fontFamily,
    minWidth: 0,
  },
  content: {
    flex: 1,
    overflow: "auto",
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: theme.spacing.lg,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "1fr",
    },
  },
  status: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: theme.spacing.xxl,
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.md,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: theme.spacing.xl,
    color: theme.colors.status.error,
  },
  empty: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: theme.spacing.xxl,
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
  },
});
