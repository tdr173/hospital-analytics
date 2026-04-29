"use client";

import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import useClasses from "@/utils/useClasses";
import { SequencePaginationStyles } from "./SequencePaginationStyles";

interface Props {
  page: number;
  rows: number;
  total: number;
  onPageChange: (page: number) => void;
  loading?: boolean;
  error?: boolean;
}

export default function SequencePagination({
  page,
  rows,
  total,
  onPageChange,
  loading = false,
  error = false,
}: Props) {
  if (loading || error) return null;
  const classes = useClasses(SequencePaginationStyles, {
    name: "SequencePagination",
  });

  const totalPages = Math.max(1, Math.ceil(total / rows));
  const fromItem = total === 0 ? 0 : (page - 1) * rows + 1;
  const toItem = Math.min(page * rows, total);

  return (
    <div className={classes.bar}>
      <span className={classes.info}>
        {total === 0
          ? "No sequences"
          : `Showing ${fromItem}–${toItem} of ${total.toLocaleString()} sequences`}
      </span>
      <div className={classes.controls}>
        <button
          type="button"
          className={classes.button}
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          <ChevronLeftIcon fontSize="small" /> Prev
        </button>
        <span className={classes.pageLabel}>
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          className={classes.button}
          disabled={page >= totalPages}
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          Next <ChevronRightIcon fontSize="small" />
        </button>
      </div>
    </div>
  );
}
