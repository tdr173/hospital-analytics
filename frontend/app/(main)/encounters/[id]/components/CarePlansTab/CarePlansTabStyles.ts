import { Theme } from "@/utils/theme";

const carePlansTabStyles = (theme: Theme) => ({
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
    // Center all headers except Description (1st) and Reason (4th)
    "& > div:not(:first-of-type):not(:nth-of-type(4))": {
      textAlign: "center" as const,
    },
  },
  dataRow: {
    borderBottom: `1px solid ${theme.colors.border.light}`,
    color: theme.colors.text.primary,
    "&:last-child": {
      borderBottom: "none",
    },
    // Fixes the CSS grid truncation issue for TruncatedText components
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
    color: theme.colors.text.secondary,
  },
  careplanCode: {
    fontFamily: "monospace",
    color: theme.colors.text.secondary,
    textAlign: "center" as const,
  },
  reasonCell: {
    color: theme.colors.text.secondary,
    minWidth: 0, // Allows text truncation to work inside this cell
  },
});

export default carePlansTabStyles;
