"use client";

import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import type { RootState } from "@/store";
import { API_BASE } from "@/store/slices/clusters/thunks";
import useClasses from "@/utils/useClasses";
import { PracticeLlmSummaryCardStyles } from "./PracticeLlmSummaryCardStyles";

export default function PracticeLlmSummaryCard() {
  const classes = useClasses(PracticeLlmSummaryCardStyles, {
    name: "PracticeLlmSummaryCard",
  });
  const providerId = useSelector((s: RootState) => s.auth.user?.providerId);
  const range = useSelector((s: RootState) => s.dashboard.selectedRange);
  const [text, setText] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<boolean>(true);

  useEffect(() => {
    if (!providerId) return;
    setLoading(true);
    setErr(null);
    fetch(
      `${API_BASE}/dashboard/practice-summary?providerId=${providerId}&range=${range}`,
      {
        headers: { "ngrok-skip-browser-warning": "true" },
      },
    )
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status}`);
        return r.json();
      })
      .then((d) => setText(d.markdown ?? ""))
      .catch(() => setErr("Could not load practice briefing."))
      .finally(() => setLoading(false));
  }, [providerId, range]);

  return (
    <div className={classes.card}>
      <button
        type="button"
        className={classes.header}
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        Practice Briefing
        <ExpandMoreIcon
          className={
            open ? `${classes.chevron} ${classes.chevronOpen}` : classes.chevron
          }
        />
      </button>
      {open && (
        <div className={classes.body}>
          {loading && "Generating briefing..."}
          {err && <span className={classes.error}>{err}</span>}
          {!loading && !err && text && (
            <pre className={classes.markdown}>
              {text.split(/(\*\*[^*]+\*\*)/g).map((seg, i) =>
                seg.startsWith("**") && seg.endsWith("**") ? (
                  <strong key={i}>{seg.slice(2, -2)}</strong>
                ) : (
                  seg
                ),
              )}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
