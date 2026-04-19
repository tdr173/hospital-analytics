"use client";

import React from "react";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import TableSortLabel from "@mui/material/TableSortLabel";
import LinearProgress from "@mui/material/LinearProgress";
import theme from "@/utils/theme";

export interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string | number;
  align?: "left" | "center" | "right";
}

interface StyledTableProps<T = any> {
  columns: Column[];
  data: T[];
  renderRow: (item: T, index: number) => React.ReactNode;
  // header
  showHeader?: boolean;
  // pagination
  showPagination?: boolean;
  total?: number;
  page?: number; // 0-indexed
  rowsPerPage?: number;
  rowsPerPageOptions?: number[];
  onPageChange?: (newPage: number) => void;
  onRowsPerPageChange?: (newRowsPerPage: number) => void;
  // sorting
  sortBy?: string;
  sortType?: "asc" | "desc";
  onSort?: (key: string, direction: "asc" | "desc") => void;
  // state
  loading?: boolean;
  emptyMessage?: string;
  stickyHeader?: boolean;
}

// Exported so consumers can use them in renderRow
export const headerCellSx = {
  backgroundColor: theme.colors.surface.containerLow,
  fontFamily: theme.typography.fontFamily,
  fontSize: "0.7rem",
  fontWeight: theme.typography.fontWeight.bold,
  color: theme.colors.text.secondary,
  textTransform: "uppercase" as const,
  letterSpacing: "0.07em",
  padding: "10px 16px",
  borderBottom: `1px solid ${theme.colors.border.main}`,
  whiteSpace: "nowrap" as const,
  userSelect: "none" as const,
  zIndex: 2,
};

export const bodyCellSx = {
  fontFamily: theme.typography.fontFamily,
  fontSize: theme.typography.fontSize.sm,
  color: theme.colors.text.primary,
  padding: "12px 16px",
  borderBottom: `1px solid ${theme.colors.border.light}`,
};

export function StyledTableRow({
  children,
  onClick,
  index,
  ...props
}: {
  children: React.ReactNode;
  onClick?: () => void;
  index?: number;
  [key: string]: any;
}) {
  const isEven = typeof index === "number" ? index % 2 === 0 : true;
  return (
    <TableRow
      onClick={onClick}
      sx={{
        backgroundColor: isEven ? "#ffffff" : "#f4f6f8",
        "&:last-child td, &:last-child th": { borderBottom: "none" },
        "&:hover": {
          backgroundColor: `${theme.colors.surface.containerLow} !important`,
        },
        cursor: onClick ? "pointer" : "default",
        transition: "background-color 0.1s ease",
      }}
      {...props}
    >
      {children}
    </TableRow>
  );
}

export default function StyledTable<T = any>({
  columns,
  data,
  renderRow,
  showHeader = true,
  showPagination = true,
  total = 0,
  page = 0,
  rowsPerPage = 10,
  rowsPerPageOptions = [5, 10, 25, 50],
  onPageChange,
  onRowsPerPageChange,
  sortBy,
  sortType = "asc",
  onSort,
  loading = false,
  emptyMessage = "No data available.",
  stickyHeader = true,
}: StyledTableProps<T>) {
  const handleSort = (key: string) => {
    if (!onSort) return;
    const newDir = sortBy === key && sortType === "asc" ? "desc" : "asc";
    onSort(key, newDir);
  };

  return (
    <Paper
      elevation={0}
      sx={{
        width: "100%",
        overflow: "hidden",
        borderRadius: theme.borderRadius.lg,
        border: `1px solid ${theme.colors.border.main}`,
        boxShadow: theme.shadows.sm,
        backgroundColor: theme.colors.surface.containerLowest,
        height: "100%",
        position: "relative",
      }}
    >
      {loading && (
        <LinearProgress
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 2,
            zIndex: 3,
            backgroundColor: "transparent",
            "& .MuiLinearProgress-bar": {
              backgroundColor: theme.colors.primary.main,
            },
          }}
        />
      )}
      <TableContainer sx={{ overflowX: "auto", height: "calc(100% - 52px)", position: "relative" }}>
        <Table
          stickyHeader={stickyHeader}
          size="small"
          sx={{ tableLayout: "fixed", width: "100%" }}
        >
          {showHeader && (
            <TableHead>
              <TableRow>
                {columns.map((col) => (
                  <TableCell
                    key={col.key}
                    align={col.align ?? "left"}
                    width={col.width}
                    sx={headerCellSx}
                    sortDirection={sortBy === col.key ? sortType : false}
                  >
                    {col.sortable ? (
                      <TableSortLabel
                        active={sortBy === col.key}
                        direction={sortBy === col.key ? sortType : "asc"}
                        onClick={() => handleSort(col.key)}
                        sx={{
                          fontSize: "inherit",
                          fontWeight: "inherit",
                          letterSpacing: "inherit",
                          color: "inherit",
                          textTransform: "inherit",
                          "&.Mui-active": { color: theme.colors.primary.main },
                          "& .MuiTableSortLabel-icon": {
                            color: `${theme.colors.primary.main} !important`,
                          },
                        }}
                      >
                        {col.label}
                      </TableSortLabel>
                    ) : (
                      col.label
                    )}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
          )}

          <TableBody>
            {data.map((item, index) => renderRow(item, index))}
          </TableBody>
        </Table>

        {data.length === 0 && (
          <div
            style={{
              position: "absolute",
              top: showHeader ? 37 : 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: theme.typography.fontFamily,
              fontSize: theme.typography.fontSize.sm,
              color: theme.colors.text.secondary,
              fontStyle: "italic",
              pointerEvents: "none",
            }}
          >
            {loading ? "Loading..." : emptyMessage}
          </div>
        )}
      </TableContainer>

      {showPagination && (
        <TablePagination
          component="div"
          count={total}
          page={page}
          rowsPerPage={rowsPerPage}
          rowsPerPageOptions={rowsPerPageOptions}
          onPageChange={(_, newPage) => onPageChange?.(newPage)}
          onRowsPerPageChange={(e) =>
            onRowsPerPageChange?.(Number(e.target.value))
          }
          showFirstButton
          showLastButton
          sx={{
            borderTop: `1px solid ${theme.colors.border.main}`,
            fontFamily: theme.typography.fontFamily,
            color: theme.colors.text.secondary,
            "& .MuiTablePagination-toolbar": {
              paddingRight: "8px",
            },
            "& .MuiTablePagination-displayedRows": {
              width: "130px",
              textAlign: "center",
              flexShrink: 0,
            },
            "& .MuiTablePagination-select, & .MuiTablePagination-displayedRows, & .MuiTablePagination-selectLabel":
              {
                fontFamily: theme.typography.fontFamily,
                fontSize: theme.typography.fontSize.sm,
                margin: 0,
              },
            "& .MuiIconButton-root": {
              color: theme.colors.text.secondary,
              "&:hover": { color: theme.colors.primary.main },
              "&.Mui-disabled": { color: theme.colors.text.disabled },
            },
          }}
        />
      )}
    </Paper>
  );
}
