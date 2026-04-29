import { Theme } from "@/utils/theme";

const conditionsTabStyles = (theme: Theme) => ({
  emptyState: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    flex: 1,
    height: "100%",
    width: "100%",
    minHeight: "200px",
    color: theme.colors.text.secondary,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    fontStyle: "italic" as const,
  },
  tableContainer: {
    width: "100%",
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    borderRadius: theme.borderRadius.md,
    height: "100%",
    overflow: "hidden",
    padding: 12,
  },
  scrollWrapper: {
    overflowY: "auto" as const,
    height: "100%",
    border: `1px solid ${theme.colors.border.main}`,
  },
  gridRow: {
    display: "grid",
    gap: "16px",
    alignItems: "center",
    padding: "12px 16px",
  },
  headerRow: {
    backgroundColor: theme.colors.surface.containerLow,
    borderBottom: `1px solid ${theme.colors.border.main}`,
    fontWeight: theme.typography.fontWeight.bold,
    color: theme.colors.text.secondary,
    textTransform: "uppercase" as const,
    letterSpacing: "0.05em",
    fontSize: "0.75rem",
    position: "sticky" as const,
    top: 0,
    zIndex: 1,
    "& > div:not(:first-of-type)": {
      textAlign: "center" as const,
    },
  },
  dataRow: {
    borderBottom: `1px solid ${theme.colors.border.light}`,
    color: theme.colors.text.primary,
    "&:last-child": {
      borderBottom: "none",
    },
    // Fixes the CSS grid truncation issue
    "& > *": {
      minWidth: 0,
    },
  },
  rowEven: {
    backgroundColor: "#ffffff",
  },
  rowOdd: {
    backgroundColor: "#f4f6f8",
  },
  centeredCell: {
    textAlign: "center" as const,
    display: "flex",
    justifyContent: "center",
  },
  conditionCode: {
    fontFamily: "monospace",
    color: theme.colors.text.secondary,
    textAlign: "center" as const,
  },
  badgeActive: {
    backgroundColor: "#e0e7ff", // Kept the indigo/blue badge for conditions
    color: "#4338ca",
    padding: "2px 8px",
    borderRadius: "12px",
    fontSize: "0.75rem",
    fontWeight: "bold" as const,
  },
  badgeResolved: {
    backgroundColor: "#f3f4f6", // Soft gray
    color: "#4b5563",
    padding: "2px 8px",
    borderRadius: "12px",
    fontSize: "0.75rem",
    fontWeight: "bold" as const,
  },
});

export default conditionsTabStyles;
