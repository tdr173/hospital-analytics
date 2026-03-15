export interface Theme {
  colors: {
    primary: {
      main: string;
      dark: string;
      light: string;
      lighter: string;
    };
    secondary: {
      main: string;
      dark: string;
      light: string;
    };
    background: {
      default: string;
      paper: string;
      alt: string;
    };
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
    border: {
      light: string;
      main: string;
      dark: string;
    };
    status: {
      success: string;
      warning: string;
      error: string;
      info: string;
    };
    grey: {
      50: string;
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  typography: {
    fontSize: {
      xs: string;
      sm: string;
      md: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      light: number;
      regular: number;
      medium: number;
      semibold: number;
      bold: number;
    };
    lineHeight: {
      tight: number;
      normal: number;
      relaxed: number;
    };
    fontFamily: string;
  };
  borderRadius: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  layout: {
    sidebarWidth: string;
    sidebarColor: string;
    headerColor: string;
    pageColor: string;
  };
}

const theme: Theme = {
  colors: {
    primary: {
      main: "#0066CC", // Medical blue
      dark: "#0052A3",
      light: "#3385DB",
      lighter: "#E6F0FF",
    },
    secondary: {
      main: "#00A651", // Healthcare green
      dark: "#008040",
      light: "#4CAF7F",
    },
    background: {
      default: "#FFFFFF",
      paper: "#F5F7FA",
      alt: "#FAFBFC",
    },
    text: {
      primary: "#1F2937",
      secondary: "#6B7280",
      disabled: "#9CA3AF",
    },
    border: {
      light: "#E5E7EB",
      main: "#D1D5DB",
      dark: "#9CA3AF",
    },
    status: {
      success: "#10B981",
      warning: "#F59E0B",
      error: "#EF4444",
      info: "#3B82F6",
    },
    grey: {
      50: "#F9FAFB",
      100: "#F3F4F6",
      200: "#E5E7EB",
      300: "#D1D5DB",
      400: "#9CA3AF",
      500: "#6B7280",
      600: "#4B5563",
    },
  },
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    xxl: "48px",
  },
  typography: {
    fontSize: {
      xs: "12px",
      sm: "14px",
      md: "16px",
      lg: "18px",
      xl: "24px",
    },
    fontWeight: {
      light: 300,
      regular: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.75,
    },
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  borderRadius: {
    xs: "2px",
    sm: "4px",
    md: "8px",
    lg: "12px",
    full: "9999px",
  },
  shadows: {
    sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    md: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
    xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
  },
  layout: {
    sidebarWidth: "200px",
    sidebarColor: "#ffffff",
    headerColor: "#ffffff",
    pageColor: "#f8f6f7",
  },
};

export default theme;
