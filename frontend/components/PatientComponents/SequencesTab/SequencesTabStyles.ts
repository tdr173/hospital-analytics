import { Theme } from "@/utils/theme";

const sequencesTabStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  countBar: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    padding: `${theme.spacing.xs} 0`,
  },
  list: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  paginationBar: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.md,
  },
  position: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
    minWidth: "120px",
    textAlign: "center" as const,
  },
  navButton: {
    color: theme.colors.primary.main,
    "&.Mui-disabled": {
      color: theme.colors.text.disabled,
    },
    "&:hover": {
      backgroundColor: "rgba(0, 103, 128, 0.08)",
    },
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    flex: 1,
    height: "100%",
    width: "100%",
    minHeight: "200px",
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
    fontSize: theme.typography.fontSize.sm,
  },
  sectionDivider: {
    borderTop: `1px solid ${theme.colors.border.light}`,
    marginTop: theme.spacing.md,
    paddingTop: theme.spacing.md,
  },
  sectionLabel: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    marginBottom: theme.spacing.sm,
  },
  continuationCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.md,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.sm,
  },
  continuationHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: theme.spacing.sm,
  },
  continuationBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    padding: "3px 10px",
    backgroundColor: "#fff7ed",
    color: "#c2410c",
    borderRadius: theme.borderRadius.full,
    fontSize: "0.65rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
  },
  matchBadge: {
    fontSize: "0.75rem",
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamilyHeading,
  },
  matchBadgeHighlight: {
    color: theme.colors.primary.main,
  },
});

export default sequencesTabStyles;
