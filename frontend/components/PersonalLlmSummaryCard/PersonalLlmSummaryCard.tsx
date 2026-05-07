"use client";

import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { apiUrl } from "@/utils/apiBases";
import useClasses from "@/utils/useClasses";
import { PersonalLlmSummaryCardStyles } from "./PersonalLlmSummaryCardStyles";

export default function PersonalLlmSummaryCard() {
  const classes = useClasses(PersonalLlmSummaryCardStyles, {
    name: "PersonalLlmSummaryCard",
  });
  const patientId = useSelector((s: RootState) => s.auth.user?.patientId);
  const [text, setText] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId) return;
    setLoading(true);
    setErr(null);
    fetch(apiUrl(`/dashboard/personal-summary?patientId=${patientId}`), {
      headers: { "ngrok-skip-browser-warning": "true" },
    })
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((d) => setText(d.markdown ?? ""))
      .catch(() => setErr("Could not load your summary right now."))
      .finally(() => setLoading(false));
  }, [patientId]);

  return (
    <div className={classes.card}>
      <div className={classes.header}>Your Health Summary</div>
      <div className={classes.body}>
        {loading && "Preparing your summary..."}
        {err && <span className={classes.error}>{err}</span>}
        {!loading && !err && text && (
          <pre className={classes.markdown}>{text}</pre>
        )}
      </div>
    </div>
  );
}
