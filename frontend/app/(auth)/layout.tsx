"use client";

import AddIcon from "@mui/icons-material/Add";
import useClasses from "@/utils/useClasses";
import { AuthLayoutStyles } from "./styles";

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const classes = useClasses(AuthLayoutStyles, { name: "AuthLayout" });

  return (
    <div className={classes.root}>
      <div className={classes.logoContainer}>
        <AddIcon
          sx={{
            color: "#191c1e",
            fontSize: "32px",
            stroke: "#191c1e",
            strokeWidth: 2,
          }}
        />
        <span className={classes.logoText}>
          HospitAI
        </span>
      </div>
      <div className={classes.body}>
        {children}
      </div>
    </div>
  );
}
