import { Theme } from "@/utils/theme";

const headerStyles = (_theme: Theme) => ({
  headerContainer: {
    backgroundColor: "white",
    height: "70px",
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0px 24px",
    borderBottom: "2px solid black",
  },
  pageTitle: {
    fontSize: "28px",
    fontWeight: 800,
    color: "#0f172a",
    fontFamily: '"Balsamiq Sans", cursive',
    lineHeight: 1,
    paddingLeft: "16px",
    borderLeft: "3px solid #0f172a",
  },
});

export default headerStyles;
