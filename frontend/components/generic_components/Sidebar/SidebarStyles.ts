import { Theme } from "@/utils/theme";

const sidebarStyles = (theme: Theme) => ({
  sidebarContainer: {
    height: "100%",
    width: theme.layout.sidebarWidth,
    flexShrink: 0,
    backgroundColor: theme.layout.sidebarColor,
    borderRight: "2px solid black",
  },
  sidebarHeader: {
    height: "70px",
    width: "100%",
    display: "flex",
    justifyContent: "space-around",
    alignItems: "center",
    gap: "8px",
    padding: "0px 8px",
  },
  headerInfo: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    gap: "4px",
    width: "auto",
  },
  tagOffset: {},
  appName: {
    fontSize: theme.typography.fontSize.lg,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    lineHeight: 1.2,
    fontFamily: '"Balsamiq Sans", cursive',
  },
  sidebarContent: {
    padding: "12px 10px",
    height: "calc(100% - 70px)",
    width: "100%",
    display: "flex",
    flexDirection: "column" as const,
    gap: "10px",
    justifyContent: "flex-start",
    alignItems: "center",
  },
  sidebarElement: {
    width: "100%",
    padding: "10px 14px",
    border: "2px solid transparent",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    cursor: "pointer",
    fontFamily: '"Balsamiq Sans", cursive',
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    backgroundColor: "white",
    boxShadow: "none",
    transition: "border-color 0.1s, box-shadow 0.1s",
    userSelect: "none" as const,
    "&:hover": {
      border: "2px solid black",
    },
    "&:active": {
      border: "2px solid black",
      boxShadow: "3px 3px 0px 0px black",
      transform: "translate(-1px, -1px)",
    },
  },
});

export default sidebarStyles;
