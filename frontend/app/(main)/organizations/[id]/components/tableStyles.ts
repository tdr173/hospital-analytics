import { Theme } from "@/utils/theme";

export const sharedTableStyles = (theme: Theme) => ({
  gridRow: {
    display: "grid",
    gap: theme.spacing.sm,
    alignItems: "center",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    fontSize: theme.typography.fontSize.sm,
  },
  headerRow: {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.7rem",
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    borderBottom: `1px solid ${theme.colors.border.main}`,
  },
  dataRow: {
    borderRadius: theme.borderRadius.sm,
  },
  rowEven: {
    backgroundColor: theme.colors.surface.containerLowest,
  },
  rowOdd: {
    backgroundColor: theme.colors.surface.containerLow,
  },
  clickableCell: {
    color: theme.colors.primary.main,
    fontWeight: theme.typography.fontWeight.semibold,
    cursor: "pointer",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  secondaryText: {
    color: theme.colors.text.secondary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100px",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
  },
  tabLoading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
    height: "100%",
  },
});
