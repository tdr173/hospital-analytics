from repository import ClusterRepository


class ClusterService:
    def __init__(self, repo: ClusterRepository):
        self.repo = repo


    def get_all_clusters(self):
        return self.repo.get_all_clusters()

    def get_cluster_statistics(self):
        return self.repo.get_cluster_statistics()

    def get_numerical_features_statistics(self):
        return self.repo.get_numerical_features_statistics()

    def get_categorical_features_statistics(self):
        return self.repo.get_categorical_features_statistics()

    def get_ai_analysis(self, cluster_id: int):
        return self.repo.get_ai_analysis(cluster_id)

