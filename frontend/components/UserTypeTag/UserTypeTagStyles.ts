import { Theme } from "@/utils/theme";

const userTypeTagStyles = (theme: Theme) => ({
  tagContainer: {
    padding: "3px 8px",
    borderRadius: theme.borderRadius.full,
    display: "inline-flex",
    alignItems: "center",
    gap: "5px",
    fontSize: theme.typography.fontSize.xs,
    fontWeight: theme.typography.fontWeight.bold,
    letterSpacing: "0.5px",
    textTransform: "uppercase" as const,
  },
  dot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
  },
});

export default userTypeTagStyles;
