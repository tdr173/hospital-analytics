import { Theme } from "@/utils/theme";

export const HomeLayoutStyles = (_theme: Theme) => ({
  layoutContainer: {
    width: "100%",
  },
});

export const HomePageStyles = (theme: Theme) => ({
  container: {
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
    fontFamily: theme.typography.fontFamily,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    width: "100%",
    minHeight: "60vh",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.md,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    width: "100%",
    minHeight: "60vh",
    color: theme.colors.status.error,
  },
  splitRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.lg,
    flexShrink: 0,
    "@media (max-width: 1100px)": {
      gridTemplateColumns: "1fr",
    },
  },
  pieSplitRow: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.lg,
    flexShrink: 0,
    "@media (max-width: 1100px)": {
      gridTemplateColumns: "1fr",
    },
  },
});
