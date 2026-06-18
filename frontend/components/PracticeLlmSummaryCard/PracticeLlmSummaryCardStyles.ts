export const PracticeLlmSummaryCardStyles = {
  card: {
    backgroundColor: "#ffffff",
    border: "1px solid #E5E7EB",
    borderRadius: "12px",
    padding: "20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    width: "100%",
    background: "none",
    border: "none",
    padding: 0,
    margin: 0,
    fontFamily: "inherit",
    fontSize: "1rem",
    fontWeight: 600,
    color: "#0F172A",
    cursor: "pointer",
    textAlign: "left" as const,
  },
  chevron: {
    transition: "transform 0.2s ease",
    color: "#64748B",
    fontSize: "1.25rem",
  },
  chevronOpen: {
    transform: "rotate(180deg)",
  },
  body: {
    color: "#334155",
    fontSize: "0.9rem",
    lineHeight: 1.55,
    marginTop: "12px",
  },
  markdown: {
    whiteSpace: "pre-wrap" as const,
    fontFamily: "inherit",
    margin: 0,
  },
  error: {
    color: "#B91C1C",
  },
};
