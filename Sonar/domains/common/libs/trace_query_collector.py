from typing import List

from thetaray.api.solution import TraceQuery


class TraceQueryCollector:
    """TraceQueryCollector builds the trace queries for the features used in the analysis

    When a feature affects dramatically on the fusion score we want to see the related transactions.
    A feature might consider only transactions made with cash in its computation, in this case the trace query should mark only the transactions that were made with cash, the other transactions should be shown but unmarked.

    Parameters
    ----------
    dataset : str
        The dataset table from which to run the query to fetch the data
    features: list
        The list of requested features
    base_query : str
        The base trace query that on top of it we want to add filtering for a feature, e.g. a feature that considers only transactions made with cash
    features_params: dict
        A configuration for the params required by the features

    Returns
    -------
    list
        A list of TraceQuery instances
    """

    def __init__(self, dataset: str, features: list, base_query: str, features_params: dict) -> None:
        self.features = features
        self.dataset = dataset
        self.base_query = base_query
        self.features_params = features_params

    def trace_queries(self) -> List[TraceQuery]:
        trace_queries = []
        global_trace_query_features = []
        for feature in self.features:
            feature_params = self.features_params[feature.identifier]
            if feature.trace_query(feature_params):
                trace_queries.append(TraceQuery(identifier=f'{feature.identifier}_tq',
                                                features=feature.output_columns,
                                                dataset=self.dataset,
                                                sql=f'{self.base_query} AND {feature.trace_query(feature_params)}'))
            else:
                global_trace_query_features.append(feature)
        global_trace_query = TraceQuery(identifier=f'features_global_tq',
                                        features=[
                                            col for feature in global_trace_query_features
                                            for col in [*feature.output_columns, feature.identifier]],
                                        dataset=self.dataset,
                                        sql=self.base_query)
        trace_queries.append(global_trace_query)
        return trace_queries

    def trace_queries_fuib(self) -> List[TraceQuery]:
        trace_queries = []
        global_trace_query_features = []
        for feature in self.features:
            feature_params = self.features_params[feature.identifier]
            if feature.trace_query(feature_params):
                trace_queries.append(TraceQuery(identifier=f'{feature.identifier}_tq',
                                                features=feature.output_columns,
                                                dataset=self.dataset,
                                                sql=f'{self.base_query} AND {feature.trace_query(feature_params)}'))
            else:
                global_trace_query_features.append(feature)
        global_trace_query = TraceQuery(identifier=f'features_global_tq',
                                        features=[
                                            col for feature in global_trace_query_features
                                            for col in [*feature.output_columns, feature.identifier]]+['cp_concentration'],
                                        dataset=self.dataset,
                                        sql=self.base_query)
        trace_queries.append(TraceQuery(identifier=f'sum_rapid_movement_tq',
                                        features=['sum_rapid_movement'],
                                        dataset=self.dataset,
                                        sql=f'{self.base_query} AND day_offset is not Null'))
        trace_queries.append(global_trace_query)
        return trace_queries
