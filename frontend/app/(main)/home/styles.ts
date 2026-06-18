import { Theme } from "@/utils/theme";

export const HomeLayoutStyles = (_theme: Theme) => ({
  layoutContainer: {
    width: "100%",
    height: "100%",
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
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.md,
    minHeight: "calc(100vh - 70px)",
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    width: "100%",
    minHeight: "calc(100vh - 70px)",
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
