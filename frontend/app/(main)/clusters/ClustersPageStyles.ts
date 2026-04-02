import { Theme } from "@/utils/theme";

const CLUSTER_COLORS = [
  "#2563EB", // blue
  "#16A34A", // green
  "#EAB308", // yellow
  "#7C3AED", // violet
  "#0891B2", // cyan
];

const OUTLIER_COLOR = "#EF4444";

export const getClusterColor = (clusterId: number, index: number) => {
  if (clusterId === -1) return OUTLIER_COLOR;
  return CLUSTER_COLORS[index % CLUSTER_COLORS.length];
};

export const ClustersPageStyles = (theme: Theme) => ({
  container: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    fontFamily: theme.typography.fontFamily,
    minWidth: 0,
  },
  tabsWrapper: {
    padding: "0 16px",
    overflow: "hidden",
    minWidth: 0,
  },
  content: {
    flex: 1,
    overflow: "auto",
    padding: theme.spacing.lg,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: theme.spacing.lg,
    "@media (max-width: 900px)": {
      gridTemplateColumns: "1fr",
    },
  },

  // Card
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.md,
    overflow: "hidden" as const,
    display: "flex",
    flexDirection: "column" as const,
    borderLeft: "4px solid transparent",
  },
  cardHeader: {
    padding: `${theme.spacing.lg} ${theme.spacing.lg} ${theme.spacing.md}`,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: theme.spacing.sm,
  },
  cardTitleArea: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "2px",
  },
  cardTitle: {
    fontFamily: theme.typography.fontFamilyHeading,
    fontWeight: theme.typography.fontWeight.bold,
    fontSize: "1.1rem",
    color: theme.colors.text.primary,
    margin: 0,
    lineHeight: theme.typography.lineHeight.tight,
  },
  cardPatientCount: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    margin: 0,
  },
  badge: {
    flexShrink: 0,
    borderRadius: theme.borderRadius.md,
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    textAlign: "center" as const,
    minWidth: "56px",
  },
  badgePercentage: {
    fontWeight: theme.typography.fontWeight.bold,
    fontSize: theme.typography.fontSize.sm,
    lineHeight: 1,
  },
  badgeLabel: {
    fontSize: "0.6rem",
    fontWeight: theme.typography.fontWeight.semibold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    lineHeight: 1.4,
  },

  // Description
  cardDescription: {
    padding: `0 ${theme.spacing.lg}`,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    lineHeight: theme.typography.lineHeight.relaxed,
    borderTop: `1px solid ${theme.colors.border.light}`,
    paddingTop: theme.spacing.md,
    margin: 0,
    flex: 1,
  },

  // Stats grid
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
  },
  statBox: {
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
  },
  statLabel: {
    fontSize: "0.65rem",
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    marginBottom: "2px",
  },
  statValue: {
    fontSize: "1.25rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
  },
  statUnit: {
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.regular,
    color: theme.colors.text.secondary,
    marginLeft: "3px",
  },

  // Insight + Recommendation
  cardFooter: {
    padding: `0 ${theme.spacing.lg} ${theme.spacing.lg}`,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.sm,
    borderTop: `1px solid ${theme.colors.border.light}`,
    paddingTop: theme.spacing.md,
  },
  footerRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: theme.spacing.sm,
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    lineHeight: theme.typography.lineHeight.normal,
  },
  footerIcon: {
    flexShrink: 0,
    width: "20px",
    height: "20px",
    marginTop: "1px",
  },
  footerLabel: {
    fontWeight: theme.typography.fontWeight.bold,
  },

  // View button
  viewButton: {
    display: "block",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    border: "none",
    borderRadius: theme.borderRadius.md,
    color: "#ffffff",
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    cursor: "pointer",
    textAlign: "center" as const,
    textDecoration: "none",
    transition: "opacity 0.15s",
    flex: 1,
    margin: 0,
    "&:hover": {
      opacity: 0.85,
    },
  },
  analyseButtonIcon: {
    width: 15,
    height: 15,
  },

  // Card action buttons row
  cardActions: {
    display: "flex",
    gap: theme.spacing.sm,
    margin: `0 ${theme.spacing.lg} ${theme.spacing.lg}`,
  },
  analyseButton: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "6px",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    border: "1.5px solid currentColor",
    borderRadius: theme.borderRadius.md,
    background: "transparent",
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.semibold,
    cursor: "pointer",
    transition: "opacity 0.15s",
    "&:hover": { opacity: 0.75 },
  },

  // Modal overlay (backdrop)
  modalOverlay: {
    position: "fixed" as const,
    inset: 0,
    backgroundColor: "rgba(15,23,42,0.55)",
    backdropFilter: "blur(4px)",
    zIndex: 1000,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
  },
  modal: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.xl,
    boxShadow: theme.shadows.xl,
    width: "100%",
    maxWidth: "860px",
    maxHeight: "90vh",
    display: "flex",
    flexDirection: "column" as const,
    overflow: "hidden",
    borderTop: "4px solid transparent",
  },

  // Modal header
  modalHeader: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    padding: `${theme.spacing.lg} ${theme.spacing.xl}`,
    backgroundColor: theme.colors.surface.containerLowest,
    borderBottom: `1px solid ${theme.colors.border.light}`,
    flexShrink: 0,
  },
  modalTitleArea: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "6px",
  },
  modalLabel: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.semibold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  modalTitle: {
    fontFamily: theme.typography.fontFamilyHeading,
    fontWeight: theme.typography.fontWeight.bold,
    fontSize: "1.2rem",
    color: theme.colors.text.primary,
    margin: 0,
    lineHeight: theme.typography.lineHeight.tight,
  },
  modalMeta: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    flexWrap: "wrap" as const,
  },
  modalPatientCount: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.secondary,
    margin: 0,
  },
  riskBadgeInline: {
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    borderRadius: theme.borderRadius.sm,
    padding: `2px 10px`,
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
  },
  riskBadgeDot: {
    width: 7,
    height: 7,
    borderRadius: "50%",
    display: "inline-block",
    flexShrink: 0,
  },
  modalCloseBtn: {
    background: theme.colors.surface.containerLow,
    border: `1px solid ${theme.colors.border.light}`,
    borderRadius: theme.borderRadius.md,
    color: theme.colors.text.secondary,
    cursor: "pointer",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "1rem",
    flexShrink: 0,
    transition: "background 0.15s",
    "&:hover": { background: theme.colors.surface.containerLow },
  },

  modalBody: {
    overflowY: "auto" as const,
    padding: `${theme.spacing.xl} ${theme.spacing.xl}`,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.xl,
  },

  // Loading inside modal
  modalLoading: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    gap: theme.spacing.md,
    padding: "56px 0",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
  },
  modalLoadingText: {
    color: theme.colors.text.secondary,
  },
  modalError: {
    color: "#dc2626",
    fontSize: "0.875rem",
    margin: 0,
  },
  spinner: {
    width: "36px",
    height: "36px",
    border: `3px solid ${theme.colors.border.light}`,
    borderTopColor: "currentColor",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },

  // Two-column grid - equal height columns
  twoCol: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.lg,
    alignItems: "stretch",
  },

  // Section
  section: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.sm,
    height: "100%",
  },
  sectionAuto: {
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.sm,
    height: "auto",
  },
  sectionTitle: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.1em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  sectionDivider: {
    height: "2px",
    borderRadius: "1px",
    marginBottom: "2px",
  },
  sectionText: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    lineHeight: theme.typography.lineHeight.relaxed,
    margin: 0,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    flex: 1,
  },

  // Characteristics - compact tag grid
  characteristicsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: theme.spacing.sm,
  },
  characteristicTag: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    lineHeight: theme.typography.lineHeight.normal,
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
    display: "flex",
    alignItems: "flex-start",
    gap: "8px",
  },
  characteristicDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    flexShrink: 0,
    marginTop: "5px",
  },

  // Numbered action items (interventions + recommendations)
  actionList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
  },
  actionItem: {
    display: "flex",
    alignItems: "flex-start",
    gap: "12px",
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.md,
  },
  actionNumber: {
    width: "22px",
    height: "22px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    flexShrink: 0,
    marginTop: "1px",
  },
  actionText: {
    fontSize: theme.typography.fontSize.sm,
    color: theme.colors.text.primary,
    lineHeight: theme.typography.lineHeight.relaxed,
    margin: 0,
  },

  // Loading / Error
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    fontSize: theme.typography.fontSize.lg,
    color: theme.colors.text.secondary,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.status.error,
    textAlign: "center" as const,
    padding: theme.spacing.xl,
  },
  empty: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: theme.spacing.xxl,
    color: theme.colors.text.secondary,
  },
});
