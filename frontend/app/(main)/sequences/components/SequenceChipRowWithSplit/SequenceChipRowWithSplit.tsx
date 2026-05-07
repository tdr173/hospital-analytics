"use client";

import React from "react";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import useClasses from "@/utils/useClasses";
import { SequenceChipRowWithSplitStyles } from "./SequenceChipRowWithSplitStyles";
import { parsePattern } from "../../utils/parsePattern";
import { colorWithAlpha } from "../../utils/colorWithAlpha";

interface Props {
  patternStr: string;
  prefixLength: number;
  colors: Record<string, string>;
}

const FALLBACK_COLOR = "#6b7280";

export default function SequenceChipRowWithSplit({
  patternStr,
  prefixLength,
  colors,
}: Props) {
  const classes = useClasses(SequenceChipRowWithSplitStyles, {
    name: "SequenceChipRowWithSplit",
  });
  const steps = parsePattern(patternStr);

  return (
    <div className={classes.wrapper}>
      <div className={classes.row}>
        {steps.map((step, stepIdx) => {
          const isMatched = stepIdx < prefixLength;
          const isFirstContinuation = stepIdx === prefixLength;
          const stepClass = isMatched
            ? classes.stepMatched
            : isFirstContinuation
              ? classes.stepFirstNext
              : classes.step;

          return (
            <React.Fragment key={stepIdx}>
              {/* Insert the NEXT divider once, just before the first continuation step */}
              {isFirstContinuation && stepIdx > 0 && (
                <span className={classes.nextPill} aria-label="continuation begins">
                  NEXT
                </span>
              )}
              <span className={stepClass}>
                {isMatched && (
                  <CheckCircleOutlineIcon
                    className={classes.checkIcon}
                    aria-hidden="true"
                  />
                )}
                {step.map((token, tokenIdx) => {
                  const color = colors[token.prefix] ?? FALLBACK_COLOR;
                  const chipStyle: React.CSSProperties = isMatched
                    ? {
                        backgroundColor: colorWithAlpha(color, 0.06),
                        color: colorWithAlpha(color, 0.7),
                        borderColor: colorWithAlpha(color, 0.2),
                        borderStyle: "dashed",
                      }
                    : isFirstContinuation
                      ? {
                          backgroundColor: colorWithAlpha(color, 0.16),
                          color,
                          borderColor: colorWithAlpha(color, 0.5),
                          boxShadow: `-3px 0 0 0 ${color}`,
                        }
                      : {
                          backgroundColor: colorWithAlpha(color, 0.12),
                          color,
                          borderColor: colorWithAlpha(color, 0.3),
                        };
                  return (
                    <span
                      key={tokenIdx}
                      className={classes.chip}
                      style={chipStyle}
                      title={`${token.prefix}: ${token.value}`}
                    >
                      <span className={classes.chipPrefix}>{token.prefix}:</span>
                      <span className={classes.chipValue}>{token.value}</span>
                    </span>
                  );
                })}
              </span>
              {stepIdx < steps.length - 1 && (
                <>
                  <span className={classes.arrow} aria-hidden="true">→</span>
                  <span className={classes.srOnly}>then</span>
                </>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
