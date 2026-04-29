import { Theme } from "@/utils/theme";

const observationsTabStyles = (theme: Theme) => ({
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
    // Center all headers except the first (Description) and the second (Value)
    "& > div:not(:first-of-type):not(:nth-of-type(2))": {
      textAlign: "center" as const,
    },
  },
  alignLeft: {
    textAlign: "left" as const, // Ensures the "Value" header aligns with the bars
  },
  dataRow: {
    borderBottom: `1px solid ${theme.colors.border.light}`,
    color: theme.colors.text.primary,
    "&:last-child": {
      borderBottom: "none",
    },
    // Fixes truncation inside CSS grids
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
  obsValueRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "flex-start", // Left aligns the bars so they form a proper visual graph
    gap: "8px",
    minWidth: 0, // Allows truncation if text fallback is used
  },
  obsBar: {
    height: "8px",
    backgroundColor: theme.colors.primary.main,
    borderRadius: "4px",
    transition: "width 0.3s ease",
  },
  cellNumeric: {
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text.primary,
  },
  cellSecondary: {
    color: theme.colors.text.secondary,
  },
});

export default observationsTabStyles;
