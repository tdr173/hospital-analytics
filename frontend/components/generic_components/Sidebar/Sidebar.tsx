"use client";

import useClasses from "@/utils/useClasses";
import sidebarStyles from "./SidebarStyles";
import AddIcon from "@mui/icons-material/Add";
import LogoutIcon from "@mui/icons-material/Logout";
import StyledButton from "../StyledButton/StyledButton";

import AnalyticsIcon from "@mui/icons-material/Analytics";
import Groups3Icon from "@mui/icons-material/Groups3";
import GroupIcon from "@mui/icons-material/Group";

import React from "react";
import { useRouter, usePathname } from "next/navigation";

const sidebarElements = [
  // { name: "Home", icon: DashboardIcon, forward: "/home" },
  // { name: "Dashboard", icon: DashboardIcon, forward: "/dashboard" },
  {
    name: "Dataset Statistics",
    icon: AnalyticsIcon,
    forward: "/statistics",
  },
  { name: "Clusters", icon: Groups3Icon, forward: "/clusters" },
  { name: "Patients", icon: GroupIcon, forward: "/patients" },
];

export default function Sidebar() {
  const classes = useClasses(sidebarStyles, { name: "SidebarStyles" });

  const router = useRouter();
  const pathname = usePathname();

  const isRouteActive = (path: string) => {
    return pathname.startsWith(path);
  };

  const sidebarElement = (
    key: number,
    Icon: React.ElementType,
    name: string,
    forward: string,
  ) => {
    return (
      <div
        key={key}
        className={classes.sidebarElement}
        style={
          isRouteActive(forward)
            ? {
                backgroundColor: "rgba(183, 234, 255, 0.2)",
                color: "#ffffff",
              }
            : undefined
        }
        onClick={() => router.push(forward)}
      >
        <Icon />
        {name}
      </div>
    );
  };

  return (
    <div className={classes.sidebarContainer}>
      <div className={classes.sidebarHeader}>
        <div className={classes.headerInfo}>
          <div className={classes.appNameRow}>
            <AddIcon
              sx={{
                color: "#ffffff",
                fontSize: "32px",
                fontWeight: "bold",
                stroke: "#ffffff",
                strokeWidth: 2,
              }}
            />
            <span className={classes.appName}>HospitAI</span>
          </div>
        </div>
      </div>
      <div className={classes.sidebarContent}>
        {sidebarElements.map((element, index) =>
          sidebarElement(index, element.icon, element.name, element.forward),
        )}
      </div>
      <div className={classes.sidebarFooter}>
        <StyledButton
          variant="ghost"
          startIcon={<LogoutIcon sx={{ fontSize: "18px !important" }} />}
          sx={{
            color: "rgba(255, 255, 255, 0.75)",
            fontSize: "0.8rem",
            padding: "6px 14px",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            "&:hover": {
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)",
              color: "#EF4444",
            },
          }}
          onClick={() => router.push("/login")}
        >
          Logout
        </StyledButton>
      </div>
    </div>
  );
}
