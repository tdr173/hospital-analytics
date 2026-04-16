import { Theme } from "@/utils/theme";
import { sharedTableStyles } from "../tableStyles";

export const ObservationsTabStyles = (theme: Theme) => ({
  ...sharedTableStyles(theme),
  obsValueRow: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  obsBar: {
    height: "6px",
    borderRadius: theme.borderRadius.full,
    backgroundColor: theme.colors.primary.light,
    minWidth: "4px",
    maxWidth: "80px",
    flexShrink: 0,
  },
});
