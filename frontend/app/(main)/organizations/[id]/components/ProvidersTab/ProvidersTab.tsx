"use client";

import useClasses from "@/utils/useClasses";
import { OrganizationProviderItem } from "@/models/generic/organizations";
import { clearName } from "@/utils/functions";
import { ProvidersTabStyles } from "./ProvidersTabStyles";
import GenderBadge from "../GenderBadge/GenderBadge";

interface Props {
  data: OrganizationProviderItem[];
  loading: boolean;
  onProviderClick: (id: string) => void;
}

export default function ProvidersTab({
  data,
  loading,
  onProviderClick,
}: Props) {
  const classes = useClasses(ProvidersTabStyles, { name: "OrgProvidersTab" });

  if (loading)
    return <div className={classes.tabLoading}>Loading clinicians...</div>;
  if (!data.length)
    return <div className={classes.emptyState}>No clinicians found.</div>;

  return (
    <div className={classes.container}>
      <div
        className={`${classes.gridRow} ${classes.providersGridRow} ${classes.headerRow}`}
      >
        <div>Name</div>
        <div>Specialty</div>
        <div>Gender</div>
        <div className={classes.utilizationHeader}>Visits</div>
      </div>
      {data.map((p, i) => (
        <div
          key={p.providerId}
          className={`${classes.gridRow} ${classes.providersGridRow} ${classes.dataRow} ${
            i % 2 === 0 ? classes.rowEven : classes.rowOdd
          }`}
        >
          <div
            className={classes.clickableCell}
            onClick={() => onProviderClick(p.providerId)}
          >
            {clearName(p.firstName, p.lastName)}
          </div>
          <div className={classes.secondaryText}>{p.speciality ?? "-"}</div>
          <div>
            <GenderBadge gender={p.gender} />
          </div>
          <div className={classes.utilizationCell}>{p.utilization}</div>
        </div>
      ))}
    </div>
  );
}
