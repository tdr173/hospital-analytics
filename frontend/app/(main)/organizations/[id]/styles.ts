import { Theme } from "@/utils/theme";

export const OrganizationDetailPageStyles = (theme: Theme) => ({
  pageContainer: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    overflow: "hidden",
    gap: theme.spacing.lg,
    padding: theme.spacing.lg,
    fontFamily: theme.typography.fontFamily,
  },
  pageLoading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.text.secondary,
  },
  pageError: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.status.error,
  },

  // Identity card
  identityCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.md,
    padding: `${theme.spacing.lg} ${theme.spacing.xl}`,
    display: "flex",
    flexWrap: "wrap" as const,
    gap: theme.spacing.lg,
    alignItems: "flex-start",
    borderLeft: `4px solid ${theme.colors.primary.main}`,
  },
  imageBlock: {
    marginRight: "16px",
  },
  avatarImage: {
    width: "78px",
    height: "78px",
  },
  nameBlock: {
    flex: "1 1 280px",
  },
  profileLabel: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: theme.colors.text.secondary,
    margin: "0 0 4px",
  },
  orgFullName: {
    fontFamily: theme.typography.fontFamilyHeading,
    fontSize: "1.5rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    margin: "0 0 8px",
  },
  badgesRow: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: theme.spacing.sm,
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.semibold,
    borderRadius: theme.borderRadius.full,
    padding: "3px 10px",
    backgroundColor: theme.colors.secondary.light,
    color: theme.colors.primary.main,
  },
  // Tabs panel
  tabsPanel: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    flex: 1,
    display: "flex",
    flexDirection: "column" as const,
    minHeight: 0,
    overflow: "hidden",
  },
  tabContentPadding: {
    padding: theme.spacing.md,
    flex: 1,
    minHeight: 0,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column" as const,
  },
  tabLoading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
    height: "100%",
  },

  // Gender badge (reused in providers sub-table)
  genderBadgeMale: {
    display: "inline-flex",
    alignItems: "center",
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.75rem",
    color: "#2563eb",
    backgroundColor: "#dbeafe",
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },
  genderBadgeFemale: {
    display: "inline-flex",
    alignItems: "center",
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.75rem",
    color: "#9333ea",
    backgroundColor: "#f3e8ff",
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },
  genderBadgeEmpty: {
    color: theme.colors.text.disabled,
  },

  // CSS grid rows (shared by both providers and encounters sub-tables)
  gridRow: {
    display: "grid",
    gap: theme.spacing.sm,
    alignItems: "center",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    fontSize: theme.typography.fontSize.sm,
  },
  providersGridRow: {
    gridTemplateColumns: "2fr 1.5fr 80px 80px",
  },
  encountersGridRow: {
    gridTemplateColumns: "1.5fr 1.5fr 90px 110px 2fr 80px",
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
  encounterTypeBadge: {
    fontSize: "0.7rem",
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.04em",
    color: theme.colors.primary.main,
    backgroundColor: theme.colors.secondary.light,
    borderRadius: theme.borderRadius.sm,
    padding: "2px 7px",
  },
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100px",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
  },

  // Encounters pagination
  encPaginationRow: {
    display: "flex",
    justifyContent: "flex-end",
    alignItems: "center",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderTop: `1px solid ${theme.colors.border.main}`,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
  },
  encPaginationBtn: {
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
