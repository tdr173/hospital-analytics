import { Theme } from "@/utils/theme";

const allergiesTabStyles = (theme: Theme) => ({
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
    // Allergen (3fr) | Recorded (1fr) | Status (1fr)
    gridTemplateColumns: "3fr 1fr 1fr",
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
  allergyActive: {
    color: "#b45309", // Amber/Brown for active
    fontSize: "0.75rem",
    fontWeight: 600,
  },
  allergyResolved: {
    color: theme.colors.text.secondary,
    fontSize: "0.75rem",
  },
});

export default allergiesTabStyles;
