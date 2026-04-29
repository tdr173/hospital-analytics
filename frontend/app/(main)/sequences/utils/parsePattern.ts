export interface ParsedPatternToken {
  prefix: string;
  value: string;
}

const SAME_DAY_GROUP_REGEX = /^\((.*)\)$/;

export function parsePattern(patternStr: string): ParsedPatternToken[][] {
  const steps = patternStr.split("->").map((s) => s.trim()).filter(Boolean);
  return steps.map((step) => {
    const groupMatch = step.match(SAME_DAY_GROUP_REGEX);
    const inner = groupMatch ? groupMatch[1] : step;
    return inner
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean)
      .map(splitPrefix);
  });
}

function splitPrefix(token: string): ParsedPatternToken {
  const colonIdx = token.indexOf(":");
  if (colonIdx === -1) return { prefix: "", value: token };
  return {
    prefix: token.slice(0, colonIdx).trim(),
    value: token.slice(colonIdx + 1).trim(),
  };
}
