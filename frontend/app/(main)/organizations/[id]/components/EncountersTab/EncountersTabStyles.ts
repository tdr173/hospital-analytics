import { Theme } from "@/utils/theme";
import { sharedTableStyles } from "../tableStyles";

export const EncountersTabStyles = (theme: Theme) => ({
  ...sharedTableStyles(theme),
  encountersGridRow: {
    gridTemplateColumns: "1.5fr 1.5fr 90px 110px 2fr 80px",
  },
  container: {
    display: "flex",
    flexDirection: "column" as const,
    flex: 1,
    minHeight: 0,
    overflow: "hidden" as const,
  },
  scroller: {
    overflow: "auto",
    flex: 1,
  },
  classBadge: {
    fontSize: "0.7rem",
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
    color: theme.colors.primary.main,
    backgroundColor: theme.colors.secondary.light,
    borderRadius: theme.borderRadius.sm,
    padding: "2px 7px",
  },
  paginationRow: {
    display: "flex",
    justifyContent: "flex-end",
    alignItems: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderTop: `1px solid ${theme.colors.border.main}`,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  paginationBtn: {
    background: "none",
    border: `1px solid ${theme.colors.border.main}`,
    borderRadius: theme.borderRadius.sm,
    padding: "3px 10px",
    cursor: "pointer",
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    "&:disabled": {
      color: theme.colors.text.disabled,
      cursor: "default",
    },
  },
});
