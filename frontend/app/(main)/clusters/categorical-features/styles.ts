import { Theme } from "@/utils/theme";

export const CategoricalFeaturesPageStyles = (theme: Theme) => ({
  container: {
    padding: "24px 16px",
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
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "24px",
  },
});
