import { Theme } from "@/utils/theme";

export const StatisticsLayoutStyles = (_theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    minWidth: 0,
  },
  tabsWrapper: {
    padding: "0 16px",
    overflow: "hidden",
    minWidth: 0,
  },
  content: {
    flex: 1,
    overflow: "hidden",
    minHeight: 0,
    padding: "0 16px",
  },
});
