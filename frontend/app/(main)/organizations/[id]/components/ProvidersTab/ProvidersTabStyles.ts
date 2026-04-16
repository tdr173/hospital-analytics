import { Theme } from "@/utils/theme";
import { sharedTableStyles } from "../tableStyles";

export const ProvidersTabStyles = (theme: Theme) => ({
  ...sharedTableStyles(theme),
  providersGridRow: {
    gridTemplateColumns: "2fr 1.5fr 80px 80px",
  },
  container: {
    overflow: "auto",
    flex: 1,
  },
  utilizationCell: {
    textAlign: "right" as const,
    color: theme.colors.text.secondary,
  },
  utilizationHeader: {
    textAlign: "right" as const,
  },
});
