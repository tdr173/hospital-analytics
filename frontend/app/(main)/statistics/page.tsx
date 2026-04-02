"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function StatisticsPage() {
  const router = useRouter();

  useEffect(() => {
    router.push("/statistics/patients");
  }, [router]);

  return <div></div>;
}
