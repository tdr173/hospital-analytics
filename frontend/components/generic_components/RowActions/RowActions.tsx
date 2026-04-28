"use client";

import IconButton from "@mui/material/IconButton";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import theme from "@/utils/theme";

interface RowActionsProps<T> {
  item: T;
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
}

export default function RowActions<T>({ item, onEdit, onDelete }: RowActionsProps<T>) {
  if (!onEdit && !onDelete) return null;
  return (
    <div style={{ display: "flex", gap: "2px", justifyContent: "flex-end" }}>
      {onEdit && (
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onEdit(item);
          }}
          aria-label="Edit"
          sx={{
            padding: "2px",
            color: theme.colors.text.secondary,
            "&:hover": { backgroundColor: "rgba(0, 103, 128, 0.08)" },
          }}
        >
          <EditOutlinedIcon sx={{ fontSize: "0.95rem" }} />
        </IconButton>
      )}
      {onDelete && (
        <IconButton
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(item);
          }}
          aria-label="Delete"
          sx={{
            padding: "2px",
            color: theme.colors.status.error,
            "&:hover": { backgroundColor: "rgba(239, 68, 68, 0.08)" },
          }}
        >
          <DeleteOutlineIcon sx={{ fontSize: "0.95rem" }} />
        </IconButton>
      )}
    </div>
  );
}
