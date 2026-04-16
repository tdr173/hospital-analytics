import { Theme } from "@/utils/theme";

export const ClusterFeaturesPageStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    fontFamily: theme.typography.fontFamily,
    minWidth: 0,
  },
  tabsWrapper: {
    padding: "0 16px",
    overflow: "hidden",
    minWidth: 0,
  },
  content: {
    flex: 1,
    overflow: "auto",
    padding: "24px 16px",
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    color: theme.colors.text.secondary,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    color: theme.colors.status.error,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "24px",
  },
});
