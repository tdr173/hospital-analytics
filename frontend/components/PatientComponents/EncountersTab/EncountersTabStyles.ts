import { Theme } from "@/utils/theme";

const encountersTabStyles = (theme: Theme) => ({
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
    display: "flex",
    flexDirection: "column" as const,
  },
  scrollWrapper: {
    overflowY: "auto" as const,
    height: "100%",
    border: `1px solid ${theme.colors.border.main}`,
    display: "flex",
    flexDirection: "column" as const,
  },
  gridRow: {
    display: "grid",
    // Date(1) | Type(1.5) | Desc(2) | Prov(2) | Org(2) | Dur(1)
    gridTemplateColumns: "0.7fr 1.5fr 2.5fr 1.5fr 2fr 0.5fr",
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
    // Center Date, Type, and Duration headers
    "& > div:nth-of-type(1), & > div:nth-of-type(2), & > div:nth-of-type(6)": {
      textAlign: "center" as const,
    },
  },
  dataRow: {
    borderBottom: `1px solid ${theme.colors.border.light}`,
    color: theme.colors.text.primary,
    "&:last-child": {
      borderBottom: "none",
    },
    "& > *": {
      minWidth: 0,
    },
  },
  rowEven: { backgroundColor: "#ffffff" },
  rowOdd: { backgroundColor: "#f4f6f8" },
  centeredCell: {
    textAlign: "center" as const,
    display: "flex",
    justifyContent: "center",
  },
  truncatedCell: {
    minWidth: 0,
    overflow: "hidden",
  },
  secondaryText: {
    color: theme.colors.text.secondary,
    minWidth: 0,
    overflow: "hidden",
  },
});

export default encountersTabStyles;
