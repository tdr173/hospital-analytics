"use client";

import useClasses from "@/utils/useClasses";
import headerStyles from "./HeaderStyles";
import StyledButton from "../StyledButton/StyledButton";
import LogoutIcon from "@mui/icons-material/Logout";

interface HeaderProps {
  pageName: string;
}

export default function Header({ pageName }: HeaderProps) {
  const classes = useClasses(headerStyles, { name: "HeaderStyles" });

  return (
    <div className={classes.headerContainer}>
      <span className={classes.pageTitle}>{pageName}</span>
      <StyledButton
        startIcon={<LogoutIcon />}
        sx={{
          color: "black",
          backgroundColor: "#E8674A",
          borderColor: "black",
          boxShadow: "3px 3px 0px 0px black",
          "&:hover": {
            backgroundColor: "#E8674A",
            borderColor: "black",
            boxShadow: "1px 1px 0px 0px black",
            transform: "translate(2px, 2px)",
          },
          "&:active": {
            backgroundColor: "#E8674A",
            boxShadow: "none",
            transform: "translate(3px, 3px)",
          },
        }}
      >
        Logout
      </StyledButton>
    </div>
  );
}
