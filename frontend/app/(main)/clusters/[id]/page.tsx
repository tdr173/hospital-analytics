"use client";

import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useParams } from "next/navigation";
import { RootState, AppDispatch } from "@/store";
import { getClusterDetail } from "@/store/slices/clusters/thunks";
import useClasses from "@/utils/useClasses";
import { ClusterDetailPageStyles } from "./styles";
import ClusterDetailHeader from "./components/ClusterDetailHeader/ClusterDetailHeader";
import ClusterVitalsCard from "./components/ClusterVitalsCard/ClusterVitalsCard";
import ClusterBurdenCard from "./components/ClusterBurdenCard/ClusterBurdenCard";
import ClusterDiseasePrevalence from "./components/ClusterDiseasePrevalence/ClusterDiseasePrevalence";
import ClusterDemographicsGrid from "./components/ClusterDemographicsGrid/ClusterDemographicsGrid";
import ClusterTopSequences from "./components/ClusterTopSequences/ClusterTopSequences";

const useAppDispatch = useDispatch.withTypes<AppDispatch>();

export default function ClusterDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const dispatch = useAppDispatch();
  const classes = useClasses(ClusterDetailPageStyles, { name: "ClusterDetailPage" });

  const { data, loading, error } = useSelector(
    (state: RootState) => state.clusterDetail,
  );

  useEffect(() => {
    if (id !== undefined) {
      dispatch(getClusterDetail(Number(id)));
    }
  }, [dispatch, id]);

  if (loading) return <div className={classes.loading}>Loading group details...</div>;
  if (error) return <div className={classes.error}>{error}</div>;
  if (!data) return <div className={classes.empty}>No group data available.</div>;

  return (
    <div className={classes.container}>
      <div className={classes.content}>
        <ClusterDetailHeader cluster={data} />
        <ClusterVitalsCard vitals={data.vitals} />
        <ClusterBurdenCard utilization={data.utilization} color={data.color} />
        <ClusterDiseasePrevalence prevalence={data.diseasePrevalence} color={data.color} />
        <ClusterDemographicsGrid demographics={data.demographics} color={data.color} />
        <ClusterTopSequences sequences={data.topSequences} color={data.color} />
      </div>
    </div>
  );
}
