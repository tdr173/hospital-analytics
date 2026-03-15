"use client";

import useClasses from "@/utils/useClasses";
import sidebarStyles from "./SidebarStyles";
import Image from "next/image";
import HospitaiLogo from "../../../public/hospitai_logo_light.svg";
import UserTypeTag from "../../UserTypeTag/UserTypeTag";

import AnalyticsIcon from "@mui/icons-material/Analytics";
import DashboardIcon from "@mui/icons-material/Dashboard";

import React from "react";
import { useRouter, usePathname } from "next/navigation";

const sidebarElements = [
  { name: "Dashboard", icon: DashboardIcon, forward: "/home" },
  { name: "Statistics", icon: AnalyticsIcon, forward: "/statistics" },
];

export default function Sidebar() {
  const classes = useClasses(sidebarStyles, { name: "SidebarStyles" });

  const router = useRouter();
  const pathname = usePathname();

  const isRouteActive = (path: string) => {
    return pathname.includes(path);
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
                border: "2px solid black",
                boxShadow: "3px 3px 0px 0px black",
                transform: "translate(-1px, -1px)",
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
        <Image src={HospitaiLogo} width={50} height={50} alt="HospitAI Logo" />
        <div className={classes.headerInfo}>
          <span className={classes.appName}>HospitAI</span>
          <div className={classes.tagOffset}>
            <UserTypeTag userType="admin" />
          </div>
        </div>
      </div>
      <div className={classes.sidebarContent}>
        {sidebarElements.map((element, index) =>
          sidebarElement(index, element.icon, element.name, element.forward),
        )}
      </div>
    </div>
  );
}
