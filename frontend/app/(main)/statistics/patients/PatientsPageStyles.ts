import { Theme } from "@/utils/theme";

export const PatientsPageStyles = (theme: Theme) => ({
  container: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.lg,
  },
  header: {
    fontFamily: theme.typography.fontFamilyHeading,
    fontSize: theme.typography.fontSize.xl,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.primary,
    marginBottom: theme.spacing.lg,
    marginTop: 0,
    letterSpacing: "-0.02em",
  },
  totalCard: {
    backgroundColor: theme.colors.surface.containerLowest,
    border: "none",
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.sm,
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
    textAlign: "center" as const,
    fontFamily: theme.typography.fontFamily,
  },
  totalLabel: {
    fontSize: theme.typography.fontSize.md,
    color: theme.colors.text.secondary,
    marginBottom: theme.spacing.xs,
  },
  totalValue: {
    fontSize: "36px",
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.primary.main,
    fontFamily: theme.typography.fontFamilyHeading,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: theme.spacing.lg,
  },
  fullWidthChart: {
    marginTop: theme.spacing.lg,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.lg,
    color: theme.colors.text.secondary,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    fontFamily: theme.typography.fontFamily,
    color: theme.colors.status.error,
    textAlign: "center" as const,
    padding: theme.spacing.xl,
  },
});
