import os
from enum import Enum
from glob import glob
from typing import List

from pyspark.sql import DataFrame
from pyspark.sql import functions as f
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from thetaray.api.graph import read_edges, read_nodes
from thetaray.api.solution.metadata_functions import get_graph
from thetaray.common import Settings
from thetaray.common.data_environment import DataEnvironment
from thetaray.common.logging import logger
from .cluster_matches import cluster_matches
from .collect_candidates import collect_candidates
from .compute_minhashes import compute_minhashes
from .find_matches import find_matches


class MatchState(Enum):
    CANDIDATE = 0
    MANUAL_CONFIRM = 1
    MANUAL_REJECT = -1
    MANUAL_CANDIDATE = 2
    AUTO_CONFIRM = 3


class EntityResolution:
    def __init__(
        self,
        context,
        graph_id: str = "public",
        account_node_id: str = "AC",
        er_edge_id: str = "ER",
        data_environment: DataEnvironment = DataEnvironment.get_default(),
    ) -> None:
        self.context = context
        self.data_environment = data_environment
        self.graph = get_graph(context, graph_id)
        self.account_node_id = account_node_id
        self.er_edge_id = er_edge_id
        self.settings = context.solution.eresolution_settings

    def account_df_transformation(self, account_df: DataFrame) -> DataFrame:
        account_df = account_df.withColumn("source_node", f.lit(None))
        return account_df

    def __load_graph(self) -> DataFrame:
        acc_data_json_schema = StructType(
            [StructField(field["field"], StringType()) for field in self.settings.matching_fields_parameters],
        )
        account_nodes = read_nodes(
            context=self.context,
            graph_identifier=self.graph.identifier,
            type=self.account_node_id,
            data_environment=self.data_environment,
        )
        account_nodes = account_nodes.select("id", "data")
        account_nodes = account_nodes.withColumn("data", f.from_json(account_nodes["data"], acc_data_json_schema))
        for field in self.settings.matching_fields_parameters:
            account_nodes = account_nodes.withColumn(field["field"], account_nodes["data"][field["field"]])
        account_nodes = account_nodes.drop("data")

        edges = read_edges(
            context=self.context,
            graph_identifier=self.graph.identifier,
            type=self.er_edge_id,
            data_environment=self.data_environment,
        )
        edge_data_json_schema = StructType(
            [
                StructField("SC", DoubleType()),
                StructField("ST", StringType()),
            ],
        )
        edges = edges.withColumn("data", f.from_json(edges["data"], edge_data_json_schema))
        edges = edges.withColumn("mean_score", edges["data"]["SC"])
        edges = edges.withColumn("ST", edges["data"]["ST"])
        graph = edges.select("id", "source_node", "mean_score", "ST").join(account_nodes, on="id")
        # if id is not int - id is full of nulls
        # previous_match = previous_match.withColumn("id", f.col("id").astype(LongType()))
        # graph.withColumn(
        #     "id", f.when(f.col("id").cast(LongType()).isNotNull(), f.col("id").cast(LongType())).otherwise(f.col("id"))
        # )
        return graph

    def load_graph(self, grouping_identifier: str, primary_identifier: str, states: List[MatchState]) -> DataFrame:
        """
            Load a graph, filter by states, rename columns, and remove parties with only one account.

            This method loads a graph, filters out rows based on the provided states, renames columns
            for primary identifiers and grouping identifiers, and removes records where a party
            has only one entry. It achieves this by first loading the graph, filtering it by the
            state column based on the provided states, renaming the 'id' column to the specified
            primary identifier, renaming the 'source_node' column to the specified grouping identifier,
            and then counting the number of rows for each grouping identifier. Finally, it filters
            out rows where the count is 1.

            Parameters
            ----------
            grouping_identifier : str
                party_id

            primary_identifier : str
                account_id

            states : list of Enum
                Available states are: MatchState.CANDIDATE, MatchState.MANUAL_CONFIRM,
                    MatchState.MANUAL_REJECT, MatchState.MANUAL_CANDIDATE, MatchState.AUTO_CONFIRM
            Returns
            -------
            pyspark.sql.DataFrame
                A DataFrame containing the filtered graph data with renamed columns. Parties with only
                one account are removed. Columns are renamed based on parameters grouping_identifier
                and primary_identifier. The DataFrame is filtered to only include rows that have a state
                value present in the states parameter.
        """
        states_int = [st.value for st in states]
        graph = self.__load_graph()
        graph = graph.filter(f.col("ST").isin(states_int))
        graph = graph.withColumnRenamed("id", primary_identifier)
        graph = graph.withColumnRenamed("source_node", grouping_identifier)
        group_counts = graph.groupBy(grouping_identifier).count()
        group_counts = group_counts.filter(f.col("count") > 1)
        graph = graph.join(group_counts, on=grouping_identifier, how="inner").drop("count")
        return graph

    def get_previous_match_result(self) -> DataFrame:
        # Load in graph in memory
        previous_match = self.__load_graph()
        previous_match = previous_match.select("id", "source_node", "mean_score")
        return previous_match

    def resolve(self, account_df: DataFrame) -> DataFrame:
        if Settings.DIRECT_SENSITIVE_DATA_ACCESS is False and Settings.DATA_ENCRYPTION is True:
            raise Exception("EMP is allowed to run only in Airflow environment / Direct Sensitive Data Access role users"
                            " with data encryption enabled")

        account_df = self.account_df_transformation(account_df)
        previous_match_df = self.get_previous_match_result()
        cliqued_account_df = account_df.join(
            previous_match_df.select("id", "source_node").withColumnRenamed("source_node", "source_node_x"),
            on="id",
            how="left",
        )
        cliqued_account_df = cliqued_account_df.withColumn("source_node", f.coalesce("source_node", "source_node_x"))
        cliqued_account_df = cliqued_account_df.drop("source_node_x")
        cliqued_account_df = cliqued_account_df.toPandas()
        previous_match_pdf = previous_match_df.toPandas()

        try:
            compute_minhashes(
                account_pdf=cliqued_account_df, chunk_size=self.settings.minhash_lsh_chunk_size,
                minhash_lsh_matching_field=self.settings.minhash_lsh_matching_field,
                minhash_lsh_ngrams=self.settings.minhash_lsh_ngrams,
                number_of_permutation=self.settings.minhash_lsh_num_permutations,
                workers=self.settings.workers,
            )
            collect_candidates(
                minhash_lsh_jaccard_threshold=self.settings.minhash_lsh_jaccard_threshold,
                workers=self.settings.workers,
                minhash_lsh_num_permutations=self.settings.minhash_lsh_num_permutations,
            )
            find_matches(
                account_pdf=cliqued_account_df, batch_size=self.settings.match_batch_size,
                matching_fields=self.settings.matching_fields_parameters,
                match_threshold=self.settings.match_threshold,
            )
            pdf = cluster_matches(account_pdf=cliqued_account_df, previous_match_pdf=previous_match_pdf)
            if pdf.empty:
                logger.info("No new matches was found during run")
            return pdf
        except Exception as e:
            raise Exception(str(e))
        finally:
            logger.info("Removing tmp files")
            for file in glob("/tmp/minhashes_*") + glob("/tmp/candidates_*") + glob("/tmp/matches_*"):
                os.remove(file)

    def load_matches_from_file(self) -> DataFrame:
        return self.context.get_spark_session().read.csv("/tmp/clustered_matches.csv")