import { Theme } from "@/utils/theme";

export const StatusBadgeStyles = (theme: Theme) => ({
  alive: {
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
  deceased: {
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
});
