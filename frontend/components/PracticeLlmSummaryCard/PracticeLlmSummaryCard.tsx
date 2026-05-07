"use client";

import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { apiUrl } from "@/utils/apiBases";
import useClasses from "@/utils/useClasses";
import { PracticeLlmSummaryCardStyles } from "./PracticeLlmSummaryCardStyles";

export default function PracticeLlmSummaryCard() {
  const classes = useClasses(PracticeLlmSummaryCardStyles, {
    name: "PracticeLlmSummaryCard",
  });
  const providerId = useSelector((s: RootState) => s.auth.user?.providerId);
  const [text, setText] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!providerId) return;
    setLoading(true);
    setErr(null);
    fetch(apiUrl(`/dashboard/practice-summary?providerId=${providerId}`), {
      headers: { "ngrok-skip-browser-warning": "true" },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((d) => setText(d.markdown ?? ""))
      .catch(() => setErr("Could not load practice briefing."))
      .finally(() => setLoading(false));
  }, [providerId]);

  return (
    <div className={classes.card}>
      <div className={classes.header}>Practice Briefing</div>
      <div className={classes.body}>
        {loading && "Generating briefing..."}
        {err && <span className={classes.error}>{err}</span>}
        {!loading && !err && text && (
          <pre className={classes.markdown}>{text}</pre>
        )}
      </div>
    </div>
  );
}
