"use client";

import useClasses from "@/utils/useClasses";
import { HomeLayoutStyles } from "./styles";

export default function HomeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const classes = useClasses(HomeLayoutStyles, { name: "HomeLayout" });
  return <div className={classes.layoutContainer}>{children}</div>;
}
