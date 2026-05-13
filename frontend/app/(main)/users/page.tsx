"use client";

import { Suspense, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchParams, useRouter } from "next/navigation";
import TableCell from "@mui/material/TableCell";
import IconButton from "@mui/material/IconButton";
import BlockIcon from "@mui/icons-material/Block";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";

import { RootState, AppDispatch } from "@/store";
import { fetchUsers, deleteUser, banUser, unbanUser } from "@/store/slices/users";
import type { UserProfileItem } from "@/store/slices/users";
import StyledTable, {
  StyledTableRow,
  bodyCellSx,
} from "@/components/generic_components/StyledTable/StyledTable";
import FormModal from "@/components/generic_components/FormModal/FormModal";
import useClasses from "@/utils/useClasses";
import { UsersPageStyles } from "./styles";
import theme from "@/utils/theme";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

const COLUMNS = [
  { key: "displayName", label: "Name", sortable: false, width: 180 },
  { key: "email", label: "Email", sortable: false, width: 220 },
  { key: "role", label: "Role", sortable: false, width: 120 },
  { key: "isActive", label: "Status", sortable: false, width: 100 },
  { key: "actions", label: "Actions", width: 110, align: "center" as const },
];

function UsersPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const dispatch = useAppDispatch();
  const classes = useClasses(UsersPageStyles, { name: "UsersPage" });

  const { items, total, loading } = useSelector((s: RootState) => s.users);

  const [deleting, setDeleting] = useState<UserProfileItem | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const page = Math.max(1, parseInt(searchParams.get("page") ?? "1", 10));
  const rows = parseInt(searchParams.get("rows") ?? "25", 10);

  useEffect(() => {
    dispatch(fetchUsers({ page, rows }));
  }, [dispatch, page, rows]);

  const setParam = (updates: Record<string, string | null>) => {
    const p = new URLSearchParams(searchParams.toString());
    Object.entries(updates).forEach(([k, v]) => {
      if (v) p.set(k, v);
      else p.delete(k);
    });
    router.push(`/users?${p.toString()}`);
  };

  const handlePageChange = (newPage: number) =>
    setParam({ page: (newPage + 1).toString() });

  const handleRowsPerPageChange = (newRows: number) =>
    setParam({ rows: newRows.toString(), page: "1" });

  const handleConfirmDelete = async () => {
    if (!deleting) return;
    setSubmitting(true);
    await dispatch(deleteUser(deleting.userId));
    setSubmitting(false);
    setDeleting(null);
  };

  const handleToggleBan = async (user: UserProfileItem) => {
    if (user.isActive) {
      await dispatch(banUser(user.userId));
    } else {
      await dispatch(unbanUser(user.userId));
    }
  };

  const roleBadgeClass = (role: string) => {
    if (role === "MANAGER") return `${classes.roleBadge} ${classes.roleBadgeManager}`;
    if (role === "DOCTOR") return `${classes.roleBadge} ${classes.roleBadgeDoctor}`;
    return `${classes.roleBadge} ${classes.roleBadgePatient}`;
  };

  const renderRow = (user: UserProfileItem, i: number) => (
    <StyledTableRow key={user.userId} index={i}>
      <TableCell sx={{ ...bodyCellSx, fontWeight: theme.typography.fontWeight.semibold }}>
        {user.displayName ?? "—"}
      </TableCell>
      <TableCell sx={bodyCellSx}>{user.email}</TableCell>
      <TableCell sx={bodyCellSx}>
        <span className={roleBadgeClass(user.role)}>{user.role}</span>
      </TableCell>
      <TableCell sx={bodyCellSx}>
        <span className={user.isActive ? classes.statusBadgeActive : classes.statusBadgeBanned}>
          {user.isActive ? "Active" : "Banned"}
        </span>
      </TableCell>
      <TableCell sx={{ ...bodyCellSx, textAlign: "center" }}>
        <IconButton
          size="small"
          title={user.isActive ? "Ban user" : "Unban user"}
          onClick={() => handleToggleBan(user)}
        >
          {user.isActive ? (
            <BlockIcon sx={{ fontSize: 18, color: theme.colors.status.error }} />
          ) : (
            <CheckCircleOutlineIcon sx={{ fontSize: 18, color: "#10b981" }} />
          )}
        </IconButton>
        <IconButton
          size="small"
          title="Delete user"
          onClick={() => setDeleting(user)}
        >
          <DeleteOutlineIcon sx={{ fontSize: 18, color: theme.colors.status.error }} />
        </IconButton>
      </TableCell>
    </StyledTableRow>
  );

  return (
    <div className={classes.pageContainer}>
      <div className={classes.tableArea}>
        {loading ? (
          <div className={classes.loading}>Loading…</div>
        ) : (
          <StyledTable
            columns={COLUMNS}
            rows={items}
            total={total}
            page={page - 1}
            rowsPerPage={rows}
            onPageChange={handlePageChange}
            onRowsPerPageChange={handleRowsPerPageChange}
            renderRow={renderRow}
            loading={loading}
          />
        )}
      </div>

      <FormModal
        open={!!deleting}
        title="Delete user"
        submitLabel="Delete"
        destructive
        submitting={submitting}
        onClose={() => setDeleting(null)}
        onSubmit={handleConfirmDelete}
      >
        <p>
          Are you sure you want to permanently delete{" "}
          <strong>{deleting?.displayName ?? deleting?.email}</strong>? This
          action cannot be undone.
        </p>
      </FormModal>
    </div>
  );
}

export default function UsersPage() {
  return (
    <Suspense>
      <UsersPageContent />
    </Suspense>
  );
}
