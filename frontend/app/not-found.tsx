"use client";

import Link from "next/link";
import useClasses from "@/utils/useClasses";
import { NotFoundStyles } from "./styles";

export default function NotFound() {
  const classes = useClasses(NotFoundStyles, { name: "NotFound" });

  return (
    <div className={classes.container}>
      <h1>404</h1>
      <p>Page not found</p>
      <Link href="/">Go home</Link>
    </div>
  );
}
