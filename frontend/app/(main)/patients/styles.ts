import { Theme } from "@/utils/theme";

export const PatientsPageStyles = (theme: Theme) => ({
  // Layout
  pageContainer: {
    display: "flex",
    flexDirection: "column" as const,
    height: "100%",
    overflow: "hidden",
    fontFamily: theme.typography.fontFamily,
  },
  tableArea: {
    flex: 1,
    overflow: "hidden",
    padding: theme.spacing.lg,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
  },

  // Gender badge
  genderBadgeEmpty: {
    color: theme.colors.text.disabled,
  },
  genderBadgeMale: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
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
    gap: "4px",
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.75rem",
    color: "#9333ea",
    backgroundColor: "#f3e8ff",
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },

  // Status badge
  statusBadgeAlive: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    color: "#166534",
    backgroundColor: "#dcfce7",
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },
  statusBadgeDeceased: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    color: "#991b1b",
    backgroundColor: "#fee2e2",
    borderRadius: theme.borderRadius.full,
    padding: "2px 9px",
  },

  // Cluster badge
  clusterBadgeEmpty: {
    color: theme.colors.text.disabled,
  },
  clusterBadgeContainer: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    overflow: "hidden",
    minWidth: 0,
  },
  clusterBadgeDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    flexShrink: 0,
  },
  clusterBadgeTitle: {
    fontSize: "0.8rem",
    color: theme.colors.text.primary,
    maxWidth: "160px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
});
