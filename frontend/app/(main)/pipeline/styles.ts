import { Theme } from "@/utils/theme";

export const PipelinePageStyles = (theme: Theme) => ({
  content: {
    flex: 1,
    overflow: "auto",
    padding: theme.spacing.lg,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.lg,
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    fontSize: theme.typography.fontSize.lg,
    color: theme.colors.text.secondary,
  },
  error: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
    width: "100%",
    color: theme.colors.status.error,
    textAlign: "center" as const,
    padding: theme.spacing.xl,
  },
  empty: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    flex: 1,
    height: "100%",
    width: "100%",
    minHeight: "200px",
    color: theme.colors.text.secondary,
    fontStyle: "italic" as const,
  },
});
