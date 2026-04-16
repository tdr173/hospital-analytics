import { Theme } from "@/utils/theme";

export const GenderBadgeStyles = (theme: Theme) => ({
  empty: {
    color: theme.colors.text.disabled,
  },
  male: {
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
  female: {
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
});
