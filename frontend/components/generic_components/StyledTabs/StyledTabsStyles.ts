import { Theme } from "@/utils/theme";

const styledTabsStyles = (theme: Theme) => ({
  tab: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.semibold,
    textTransform: "uppercase" as const,
    color: theme.colors.text.secondary,
    backgroundColor: "transparent",
    border: "none",
    borderBottom: "2px solid transparent",
    borderRadius: "0",
    padding: "10px 6px",
    minHeight: "unset",
    minWidth: "unset",
    cursor: "pointer",
    transition: "color 0.15s, border-color 0.15s",
    letterSpacing: "0.3px",
    whiteSpace: "nowrap" as const,
    "&:hover": {
      backgroundColor: "transparent",
      color: theme.colors.text.primary,
    },
  },
  activeTab: {
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    color: theme.colors.primary.light,
    backgroundColor: "transparent",
    border: "none",
    borderBottom: `2px solid ${theme.colors.primary.light}`,
    borderRadius: "0",
    padding: "10px 8px",
    minHeight: "unset",
    minWidth: "unset",
    cursor: "pointer",
    letterSpacing: "0.3px",
    whiteSpace: "nowrap" as const,
    "&:hover": {
      backgroundColor: "transparent",
      color: theme.colors.primary.light,
    },
  },
});

export default styledTabsStyles;
