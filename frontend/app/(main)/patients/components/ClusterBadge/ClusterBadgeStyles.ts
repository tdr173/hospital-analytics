import { Theme } from "@/utils/theme";

export const ClusterBadgeStyles = (theme: Theme) => ({
  empty: {
    color: theme.colors.text.disabled,
  },
  container: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    overflow: "hidden",
    minWidth: 0,
  },
  dot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    flexShrink: 0,
  },
});
