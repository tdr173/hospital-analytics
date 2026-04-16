import { Theme } from "@/utils/theme";

export const ClusterStatisticsPageStyles = (theme: Theme) => ({
  container: {
    padding: "24px 16px",
    display: "flex",
    flexDirection: "column" as const,
    gap: "24px",
    fontFamily: theme.typography.fontFamily,
    height: "100%",
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.text.secondary,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    color: theme.colors.status.error,
  },
  imageCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.md,
  },
  imageTitle: {
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.md,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
    margin: "0 0 8px 0",
  },
  cardImage: {
    width: "100%",
    borderRadius: theme.borderRadius.md,
    display: "block",
  },
  imageFallback: {
    padding: theme.spacing.lg,
    color: theme.colors.text.secondary,
    fontSize: theme.typography.fontSize.sm,
    textAlign: "center" as const,
  },
});
