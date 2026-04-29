"use client";

import React from "react";
import useClasses from "@/utils/useClasses";
import { SequenceChipRowStyles } from "./SequenceChipRowStyles";
import { parsePattern } from "../../utils/parsePattern";
import { colorWithAlpha } from "../../utils/colorWithAlpha";

interface Props {
  patternStr: string;
  colors: Record<string, string>;
}

const FALLBACK_COLOR = "#6b7280";

export default function SequenceChipRow({ patternStr, colors }: Props) {
  const classes = useClasses(SequenceChipRowStyles, { name: "SequenceChipRow" });
  const steps = parsePattern(patternStr);

  return (
    <div className={classes.wrapper}>
    <div className={classes.row}>
      {steps.map((step, stepIdx) => (
        <React.Fragment key={stepIdx}>
          <span className={classes.step}>
            {step.map((token, tokenIdx) => {
              const color = colors[token.prefix] ?? FALLBACK_COLOR;
              return (
                <span
                  key={tokenIdx}
                  className={classes.chip}
                  style={{
                    backgroundColor: colorWithAlpha(color, 0.12),
                    color,
                    borderColor: colorWithAlpha(color, 0.3),
                  }}
                >
                  <span className={classes.chipPrefix}>{token.prefix}:</span>
                  <span className={classes.chipValue}>{token.value}</span>
                </span>
              );
            })}
          </span>
          {stepIdx < steps.length - 1 && (
            <span className={classes.arrow}>→</span>
          )}
        </React.Fragment>
      ))}
    </div>
    </div>
  );
}
