import { Theme } from "@/utils/theme";

export const MainLayoutStyles = (theme: Theme) => ({
  root: {
    display: "flex",
    height: "100vh",
    backgroundColor: theme.layout.pageColor,
  },
  main: {
    display: "flex",
    flexDirection: "column" as const,
    flex: 1,
    minWidth: 0,
    overflow: "hidden",
    position: "relative" as const,
    marginLeft: theme.layout.sidebarWidth,
  },
  content: {
    flex: 1,
    overflow: "auto",
    backgroundColor: theme.layout.pageColor,
  },
  chatPanel: {
    width: "25%",
    minWidth: "300px",
    height: "100vh",
    flexShrink: 0,
    borderLeft: `1px solid ${theme.colors.border.light}`,
  },
});
