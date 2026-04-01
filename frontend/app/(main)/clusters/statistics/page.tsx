"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getClusterStatistics } from "@/store/slices/clusters/thunks";
import ScatterPlotComponent from "@/components/generic_components/ScatterPlotComponent/ScatterPlotComponent";
import useClasses from "@/utils/useClasses";
import { ClusterStatisticsPageStyles } from "./styles";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ClusterStatisticsPage() {
  const { data, loading, error } = useSelector(
    (state: RootState) => state.pcaScatter,
  );
  const dispatch = useAppDispatch();
  const classes = useClasses(ClusterStatisticsPageStyles, { name: "ClusterStatisticsPage" });

  useEffect(() => {
    if (!data) dispatch(getClusterStatistics());
  }, [dispatch]);

  return (
    <div className={classes.container}>
      {loading && (
        <div className={classes.loading}>
          Loading...
        </div>
      )}
      {error && (
        <div className={classes.error}>
          {error}
        </div>
      )}
      {data && (
        <>
          <ScatterPlotComponent
            points={data.points}
            title="Patient Clusters: PCA Projection"
            clusterColors={data.cluster_colors}
          />

          <div className={classes.heatmapCard}>
            <p className={classes.heatmapTitle}>
              Cluster Heatmap
            </p>
            {data.heatmap && (
              <img
                src={`data:image/png;base64,${data.heatmap}`}
                alt="Cluster Heatmap"
                className={classes.heatmapImage}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
