import { Theme } from "@/utils/theme";

const styledTabsStyles = (_theme: Theme) => ({
  tab: {
    fontFamily: '"Balsamiq Sans", cursive',
    fontSize: "12px",
    fontWeight: 700,
    textTransform: "none" as const,
    color: "#1f2937",
    backgroundColor: "white",
    border: "2px solid black",
    borderRadius: "8px",
    padding: "4px 10px",
    minHeight: "unset",
    minWidth: "unset",
    flex: 1,
    cursor: "pointer",
    transition: "background-color 0.1s",
    "&:hover": {
      backgroundColor: "#f0f0f0",
    },
  },
  activeTab: {
    fontFamily: '"Balsamiq Sans", cursive',
    fontSize: "12px",
    fontWeight: 700,
    textTransform: "none" as const,
    color: "#1f2937",
    backgroundColor: "#d4edda",
    border: "2px solid black",
    borderRadius: "8px",
    padding: "4px 10px",
    minHeight: "unset",
    minWidth: "unset",
    flex: 1,
    cursor: "pointer",
    "&:hover": {
      backgroundColor: "#d4edda",
    },
  },
});

export default styledTabsStyles;
