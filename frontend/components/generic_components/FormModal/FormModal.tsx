"use client";

import { ReactNode, useEffect } from "react";
import StyledButton from "@/components/generic_components/StyledButton/StyledButton";
import useClasses from "@/utils/useClasses";
import FormModalStyles from "./FormModalStyles";
import theme from "@/utils/theme";

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

  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Enter" && !submitting) {
        e.preventDefault();
        onSubmit();
      }
      if (e.key === "Escape") {
        onClose();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, submitting, onSubmit, onClose]);

  if (!open) return null;

  return (
    <div className={classes.overlay} onClick={onClose}>
      <div className={classes.modal} onClick={(e) => e.stopPropagation()}>
        <div className={classes.header}>
          <div className={classes.title}>{title}</div>
          <button
            className={classes.closeBtn}
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className={layout === "grid" ? classes.body : classes.bodySingle}>
          {children}
        </div>

        {errorMessage ? (
          <div className={classes.errorText}>{errorMessage}</div>
        ) : null}

        <div className={classes.footer}>
          <span></span>
          <span></span>
          <StyledButton
            variant="secondary"
            onClick={onClose}
            disabled={submitting}
            sx={{
              flex: 1,
              backgroundColor: theme.colors.button.cancel,
              color: "#ffffff",
              border: "none",
              boxShadow: "none",
              padding: "8px 18px",
              "&:hover": {
                backgroundColor: theme.colors.button.cancelHover,
                boxShadow: "none",
              },
              "&:active": {
                backgroundColor: theme.colors.button.cancelActive,
                boxShadow: "none",
              },
            }}
          >
            {cancelLabel}
          </StyledButton>
          <StyledButton
            variant="secondary"
            onClick={onSubmit}
            disabled={submitting}
            sx={
              destructive
                ? {
                    flex: 1,
                    backgroundColor: theme.colors.button.delete,
                    color: "#ffffff",
                    border: "none",
                    boxShadow: "none",
                    padding: "8px 18px",
                    "&:hover": {
                      backgroundColor: theme.colors.button.deleteHover,
                      boxShadow: "none",
                    },
                    "&:active": {
                      backgroundColor: theme.colors.button.deleteActive,
                      boxShadow: "none",
                    },
                  }
                : {
                    flex: 1,
                    backgroundColor: theme.colors.button.add,
                    color: "#ffffff",
                    border: "none",
                    boxShadow: "none",
                    padding: "8px 18px",
                    "&:hover": {
                      backgroundColor: theme.colors.button.addHover,
                      boxShadow: "none",
                    },
                    "&:active": {
                      backgroundColor: theme.colors.button.addActive,
                      boxShadow: "none",
                    },
                  }
            }
          >
            {submitting ? "Saving..." : submitLabel}
          </StyledButton>
        </div>
      </div>
    </div>
  );
}
