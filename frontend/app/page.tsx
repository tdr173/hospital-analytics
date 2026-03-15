"use client";

import Sidebar from "@/components/generic_components/Sidebar/Sidebar";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push("/home");
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh" }}>
      <Sidebar />
    </div>
  );
}
