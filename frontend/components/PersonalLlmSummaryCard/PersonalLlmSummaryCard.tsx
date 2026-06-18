"use client";

import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import { API_BASE } from "@/store/slices/clusters/thunks";
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
    fetch(`${API_BASE}/dashboard/personal-summary?patientId=${patientId}`, {
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
          <div className={classes.markdown}>
            {text.split("\n").map((line, i) => {
              const parts = line.split(/(\*\*[^*]+\*\*)/g).map((seg, j) =>
                seg.startsWith("**") && seg.endsWith("**")
                  ? <strong key={j}>{seg.slice(2, -2)}</strong>
                  : seg
              );
              return <p key={i} className={classes.line}>{parts}</p>;
            })}
          </div>
        )}
      </div>
    </div>
  );
}
