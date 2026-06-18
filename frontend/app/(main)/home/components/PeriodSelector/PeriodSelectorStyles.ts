import { Theme } from "@/utils/theme";

export const PeriodSelectorStyles = (theme: Theme) => ({
  rangeGroup: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "2px",
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    border: `1px solid ${theme.colors.border.main}`,
    alignSelf: "flex-start",
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
});
