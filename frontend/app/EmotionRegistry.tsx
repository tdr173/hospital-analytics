"use client";

import { useRef } from "react";
import { useServerInsertedHTML } from "next/navigation";
import { cache } from "@emotion/css";

export default function EmotionRegistry({ children }: { children: React.ReactNode }) {
  const inserted = useRef(new Set<string>());

  useServerInsertedHTML(() => {
    const entries = Object.entries(cache.inserted);
    const newEntries = entries.filter(([key]) => !inserted.current.has(key));
    if (newEntries.length === 0) return null;

    let styles = "";
    newEntries.forEach(([key, value]) => {
      inserted.current.add(key);
      if (typeof value === "string") {
        styles += value;
      }
    });

    if (!styles) return null;

    return (
      <style
        key={cache.key}
        data-emotion={`${cache.key} ${newEntries.map(([k]) => k).join(" ")}`}
        dangerouslySetInnerHTML={{ __html: styles }}
      />
    );
  });

  return <>{children}</>;
}
