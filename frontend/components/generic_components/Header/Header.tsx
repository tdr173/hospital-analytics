"use client";

import useClasses from "@/utils/useClasses";
import headerStyles from "./HeaderStyles";
import StyledButton from "../StyledButton/StyledButton";
import LogoutIcon from "@mui/icons-material/Logout";
import { usePathname } from "next/navigation";

const HeaderMap: Record<string, string> = {
  home: "Home",
  statistics: "Dataset Statistics",
};

function capitalize(str: string) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export default function Header() {
  const classes = useClasses(headerStyles, { name: "HeaderStyles" });
  const pathname = usePathname();
  const parts = pathname.split("/").filter((part) => part !== "");

  const title = parts
    .map((part) => HeaderMap[part] || capitalize(part))
    .join(" — ");

  return (
    <div className={classes.headerContainer}>
      <span className={classes.pageTitle}>{title}</span>
      <StyledButton
        variant="ghost"
        startIcon={<LogoutIcon sx={{ fontSize: "18px !important" }} />}
        sx={{
          color: "#EF4444",
          fontSize: "0.8rem",
          padding: "6px 14px",
          "&:hover": {
            backgroundColor: "rgba(239, 68, 68, 0.06)",
            border: "1px solid rgba(239, 68, 68, 0.2)",
            color: "#DC2626",
          },
        }}
      >
        Logout
      </StyledButton>
    </div>
  );
}
