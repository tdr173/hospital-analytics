import theme from "@/utils/theme";

const FormModalStyles = {
  overlay: {
    position: "fixed" as const,
    inset: 0,
    backgroundColor: "rgba(15, 23, 42, 0.45)",
    zIndex: 1300,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: theme.spacing.lg,
  },
  modal: {
    backgroundColor: theme.colors.surface.containerLowest,
    borderRadius: theme.borderRadius.lg,
    boxShadow: theme.shadows.lg,
    width: "100%",
    maxWidth: "640px",
    maxHeight: "90vh",
    display: "flex",
    flexDirection: "column" as const,
    overflow: "hidden" as const,
    transition: "max-width 0.2s ease", // Smooth transition if it changes
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border.main}`,
  },
  title: {
    fontFamily: theme.typography.fontFamily,
    fontWeight: theme.typography.fontWeight.semibold,
    fontSize: "1.05rem",
    color: theme.colors.text.primary,
  },
  closeBtn: {
    background: "transparent",
    border: "none",
    color: theme.colors.text.secondary,
    fontSize: "1.4rem",
    cursor: "pointer",
    padding: "4px 8px",
    borderRadius: theme.borderRadius.sm,
    "&:hover": { backgroundColor: theme.colors.surface.containerLow },
  },
  body: {
    padding: theme.spacing.lg,
    overflowY: "auto" as const,
    display: "grid",
    gridTemplateColumns: "1fr 1fr", // 2 Columns
    gap: theme.spacing.md,
  },
  bodyThree: {
    padding: theme.spacing.lg,
    overflowY: "auto" as const,
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr", // 3 Columns
    gap: theme.spacing.md,
  },
  bodySingle: {
    padding: theme.spacing.lg,
    overflowY: "auto" as const,
    display: "flex",
    flexDirection: "column" as const,
    gap: theme.spacing.md,
  },
  fieldFull: {
    gridColumn: "1 / -1",
  },
  field: {
    display: "flex",
    flexDirection: "column" as const,
    minHeight: "80px",
  },
  footer: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr 1fr",
    gap: theme.spacing.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderTop: `1px solid ${theme.colors.border.main}`,
    backgroundColor: theme.colors.surface.containerLow,
  },
  errorText: {
    color: theme.colors.status.error,
    fontFamily: theme.typography.fontFamily,
    fontSize: "0.8rem",
    paddingLeft: theme.spacing.lg,
    paddingRight: theme.spacing.lg,
    paddingBottom: theme.spacing.sm,
  },
};

export default FormModalStyles;
