"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { RootState, AppDispatch } from "@/store";
import { getClusterStatistics } from "@/store/slices/clusters/thunks";
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
          <div className={classes.imageCard}>
            <p className={classes.imageTitle}>Patient Clusters: PCA Projection</p>
            {data.pcaImage ? (
              <img
                src={`data:image/png;base64,${data.pcaImage}`}
                alt="PCA Projection"
                className={classes.cardImage}
              />
            ) : (
              <div className={classes.imageFallback}>
                PCA image not available. Re-run the clustering pipeline to generate it.
              </div>
            )}
          </div>

          <div className={classes.imageCard}>
            <p className={classes.imageTitle}>Cluster Heatmap</p>
            {data.heatmap && (
              <img
                src={`data:image/png;base64,${data.heatmap}`}
                alt="Cluster Heatmap"
                className={classes.cardImage}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
