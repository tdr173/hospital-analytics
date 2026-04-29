"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getClustersOverview } from "@/store/slices/clusters/thunks";
import useClasses from "@/utils/useClasses";
import { ClusterSummariesPageStyles } from "./styles";
import ClusterCard from "./components/ClusterCard/ClusterCard";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ClusterSummariesPage() {
  const dispatch = useAppDispatch();
  const classes = useClasses(ClusterSummariesPageStyles, {
    name: "ClusterSummariesPage",
  });

  const { data, loading, error } = useSelector(
    (state: RootState) => state.clusters,
  );

  useEffect(() => {
    dispatch(getClustersOverview());
  }, [dispatch]);

  if (loading) return <div className={classes.loading}>Loading patient groups...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data || data.clusters.length === 0)
    return <div className={classes.empty}>No patient groups available.</div>;

  return (
    <div className={classes.content}>
      <div className={classes.grid}>
        {data.clusters.map((cluster) => (
          <ClusterCard key={cluster.clusterId} cluster={cluster} />
        ))}
      </div>
    </div>
  );
}
