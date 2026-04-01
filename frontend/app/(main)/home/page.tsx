"use client";

import useClasses from "@/utils/useClasses";
import { HomePageStyles } from "./styles";

export default function HomePage() {
  const classes = useClasses(HomePageStyles, { name: "HomePage" });
  return <div className={classes.container}></div>;
}
