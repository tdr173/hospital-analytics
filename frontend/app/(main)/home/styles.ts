import { Theme } from "@/utils/theme";

export const HomeLayoutStyles = (_theme: Theme) => ({
  layoutContainer: {
    display: "flex",
    height: "100vh",
  },
});

export const HomePageStyles = (theme: Theme) => ({
  container: {
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
    height: "100%",
    overflow: "auto",
    fontFamily: theme.typography.fontFamily,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.md,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.status.error,
  },

  // KPI row
  kpiRow: {
    display: "grid",
    gridTemplateColumns: "repeat(5, 1fr)",
    gap: theme.spacing.md,
    flexShrink: 0,
  },
  kpiCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.xs,
    borderTop: `3px solid ${theme.colors.primary.main}`,
  },
  kpiIconRow: {
    display: "flex",
    alignItems: "center",
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.xs,
  },
  kpiLabel: {
    fontSize: "0.68rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.07em",
    color: theme.colors.text.secondary,
    margin: 0,
  },
  kpiValue: {
    fontSize: "1.8rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    fontFamily: theme.typography.fontFamilyHeading,
    margin: 0,
    lineHeight: 1.1,
  },
  kpiSub: {
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.primary.main,
    fontWeight: theme.typography.fontWeight.medium,
    margin: 0,
  },

  // Chart row
  chartRow: {
    display: "grid",
    gridTemplateColumns: "3fr 2fr",
    gap: theme.spacing.lg,
    flexShrink: 0,
  },
  card: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
  },
  cardTitle: {
    fontSize: "0.7rem",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.07em",
    margin: `0 0 ${theme.spacing.md} 0`,
  },

  // Bottom row
  bottomRow: {
    display: "grid",
    gridTemplateColumns: "1fr 2fr",
    gap: theme.spacing.lg,
    flexShrink: 0,
  },
  demographicsCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
  },
  demographicsSectionTitle: {
    fontSize: "0.68rem",
    fontWeight: theme.typography.fontWeight.bold,
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    margin: `0 0 ${theme.spacing.sm} 0`,
  },

  // Recent encounters
  recentCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
  },
  recentGrid: {
    display: "grid",
    gridTemplateColumns: "1.5fr 1.2fr 1.2fr 90px 120px 1.5fr",
    gap: theme.spacing.sm,
    alignItems: "center",
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    fontSize: theme.typography.fontSize.sm,
  },
  recentHeader: {
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "0.68rem",
    textTransform: "uppercase" as const,
    letterSpacing: "0.06em",
    color: theme.colors.text.secondary,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    marginBottom: theme.spacing.xs,
  },
  recentRowEven: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.sm,
  },
  recentRowOdd: {
    backgroundColor: theme.colors.surface.containerLow,
    borderRadius: theme.borderRadius.sm,
  },
  recentClickable: {
    color: theme.colors.primary.main,
    fontWeight: theme.typography.fontWeight.semibold,
    cursor: "pointer",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  recentSecondary: {
    color: theme.colors.text.secondary,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
  encounterTypeBadge: {
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
