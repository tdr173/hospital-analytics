import { Theme } from "@/utils/theme";

export const StatisticsLayoutStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    minWidth: 0,
  },
  topBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "8px 16px 0 16px",
    gap: theme.spacing.md,
    minWidth: 0,
  },
  tabsWrapper: {
    flex: 1,
    overflow: "hidden",
    minWidth: 0,
  },
  rangeGroup: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    padding: "2px",
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    border: `1px solid ${theme.colors.border.main}`,
  },
  rangeButton: {
    padding: "4px 12px",
    border: "none",
    backgroundColor: "transparent",
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.72rem",
    fontWeight: theme.typography.fontWeight.semibold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    cursor: "pointer",
    borderRadius: theme.borderRadius.sm,
    transition: "background-color 0.15s, color 0.15s",
    "&:hover": {
      color: theme.colors.text.primary,
    },
  },
  rangeButtonActive: {
    backgroundColor: theme.colors.primary.main,
    color: "#ffffff",
    "&:hover": {
      color: "#ffffff",
    },
  },
  content: {
    flex: 1,
    overflow: "hidden",
    minHeight: 0,
    padding: "0 16px",
  },
});
