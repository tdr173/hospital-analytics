import { Theme } from "@/utils/theme";

export const RecentEncountersTableStyles = (theme: Theme) => ({
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
  },
  title: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.07em",
    margin: `0 0 ${theme.spacing.md} 0`,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1.5fr 1.2fr 1.2fr 90px 120px 1.5fr 56px",
    gap: theme.spacing.sm,
    alignItems: "center",
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    fontSize: theme.typography.fontSize.sm,
  },
  actionsCell: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  actionsHeader: {
    textAlign: "center" as const,
  },
  actionButton: {
    padding: "4px",
    color: theme.colors.primary.main,
    "&:hover": {
      backgroundColor: "rgba(0, 103, 128, 0.08)",
    },
  },
  header: {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.68rem",
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    marginBottom: theme.spacing.xs,
  },
  rowEven: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.sm,
  },
  rowOdd: {
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.sm,
  },
  clickable: {
    color: theme.colors.primary.main,
    fontWeight: theme.typography.fontWeight.semibold,
    cursor: "pointer",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  secondary: {
    color: theme.colors.text.secondary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  classBadge: {
    fontSize: "0.65rem",
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
    color: theme.colors.primary.main,
    backgroundColor: theme.colors.secondary.light,
    borderRadius: theme.borderRadius.sm,
    padding: "2px 6px",
    whiteSpace: "nowrap" as const,
    display: "inline-block",
  },
});
