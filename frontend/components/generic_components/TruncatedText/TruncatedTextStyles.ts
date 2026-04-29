import { Theme } from "@/utils/theme";

export const TruncatedTextStyles = (_theme: Theme) => ({
  text: {
    display: "block",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap" as const,
  },
});
