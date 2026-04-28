"use client";

import { ReactNode } from "react";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import FormModalStyles from "./FormModalStyles";

interface FormModalProps {
  open: boolean;
  title: string;
  submitLabel?: string;
  cancelLabel?: string;
  submitting?: boolean;
  onClose: () => void;
  onSubmit: () => void;
  children: ReactNode;
  layout?: "grid" | "single";
  destructive?: boolean;
  errorMessage?: string | null;
}

export default function FormModal({
  open,
  title,
  submitLabel = "Save",
  cancelLabel = "Cancel",
  submitting = false,
  onClose,
  onSubmit,
  children,
  layout = "grid",
  destructive = false,
  errorMessage,
}: FormModalProps) {
  const classes = useClasses(FormModalStyles, { name: "FormModal" });

  if (!open) return null;

  return (
    <div className={classes.overlay} onClick={onClose}>
      <div className={classes.modal} onClick={(e) => e.stopPropagation()}>
        <div className={classes.header}>
          <div className={classes.title}>{title}</div>
          <button className={classes.closeBtn} onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className={layout === "grid" ? classes.body : classes.bodySingle}>
          {children}
        </div>

        {errorMessage ? <div className={classes.errorText}>{errorMessage}</div> : null}

        <div className={classes.footer}>
          <StyledButton variant="secondary" onClick={onClose} disabled={submitting}>
            {cancelLabel}
          </StyledButton>
          <StyledButton
            variant={destructive ? "secondary" : "primary"}
            onClick={onSubmit}
            disabled={submitting}
            sx={destructive ? { color: "#b91c1c", borderColor: "#b91c1c" } : undefined}
          >
            {submitting ? "Saving..." : submitLabel}
          </StyledButton>
        </div>
      </div>
    </div>
  );
}
