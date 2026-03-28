"use client";

import Button, { ButtonProps } from "@mui/material/Button";

interface StyledButtonProps extends ButtonProps {
  variant?: "primary" | "secondary" | "ghost";
}

export default function StyledButton({
  variant = "primary",
  children,
  sx,
  ...props
}: StyledButtonProps) {
  const variantStyles = {
    primary: {
      background: "linear-gradient(135deg, #191c1e 0%, #028fb0 100%)",
      color: "#ffffff",
      border: "none",
      boxShadow: "0px 2px 8px rgba(25, 28, 30, 0.12)",
      "&:hover": {
        background: "linear-gradient(135deg, #2a2d30 0%, #039fc4 100%)",
        boxShadow: "0px 4px 16px rgba(25, 28, 30, 0.16)",
        transform: "translateY(-1px)",
      },
      "&:active": {
        background: "linear-gradient(135deg, #0f1112 0%, #027a98 100%)",
        boxShadow: "0px 1px 4px rgba(25, 28, 30, 0.1)",
        transform: "translateY(0)",
      },
    },
    secondary: {
      backgroundColor: "transparent",
      color: "#191c1e",
      border: "1px solid rgba(198, 198, 205, 0.35)",
      boxShadow: "none",
      "&:hover": {
        backgroundColor: "rgba(0, 103, 128, 0.04)",
        borderColor: "rgba(198, 198, 205, 0.5)",
      },
    },
    ghost: {
      backgroundColor: "transparent",
      color: "#191c1e",
      border: "1px solid transparent",
      boxShadow: "none",
      "&:hover": {
        backgroundColor: "rgba(0, 103, 128, 0.04)",
        border: "1px solid rgba(198, 198, 205, 0.35)",
      },
    },
  };

  return (
    <Button
      disableRipple
      disableElevation
      {...props}
      sx={{
        fontFamily: '"Inter", sans-serif',
        fontWeight: 600,
        fontSize: "0.875rem",
        textTransform: "none",
        borderRadius: "6px",
        padding: "8px 18px",
        transition: "all 0.2s ease",
        minWidth: "unset",
        ...variantStyles[variant],
        ...sx,
      }}
    >
      {children}
    </Button>
  );
}
