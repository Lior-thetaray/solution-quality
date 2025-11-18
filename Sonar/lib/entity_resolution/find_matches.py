import concurrent.futures
import glob
from typing import Any, Dict, List

from fastDamerauLevenshtein import damerauLevenshtein
import pandas as pd
from pyspark.sql import DataFrame

from thetaray.common.logging import logger


def __find_matches(
    indexed_accounts_pdf: pd.DataFrame,
    f_index: int,
    candidates_file: str,
    matching_fields: List[Dict[str, Any]],
    match_threshold: float,
    batch_size: int = 20_000,
) -> None:
    logger.info(f"Matching candidates file {candidates_file}")
    read_kwargs = {}
    if indexed_accounts_pdf.index.inferred_type == 'string':
        logger.info("Changing_types") 
        read_kwargs['dtype'] = {"id_a": str, 'id_b': str}
    all_candidates_pdf = pd.read_csv(candidates_file, **read_kwargs)
    all_candidates_pdf = all_candidates_pdf.reset_index(drop=True)

    batches = [all_candidates_pdf[i:i + batch_size] for i in range(0, all_candidates_pdf.shape[0], batch_size)]

    matches_list = list()

    for candidates_pdf in batches:
        candidates_pdf = candidates_pdf.merge(indexed_accounts_pdf, left_on="id_a", right_on="id")

        rename_dict = dict()
        for f in matching_fields:
            rename_dict[f["field"]] = f["field"] + "_a"
            if "normalized" in f:
                rename_dict[f["normalized"]] = f["normalized"] + "_a"

        candidates_pdf = candidates_pdf.rename(columns=rename_dict)
        candidates_pdf = candidates_pdf.merge(indexed_accounts_pdf, left_on="id_b", right_on="id")

        rename_dict = dict()
        for f in matching_fields:
            rename_dict[f["field"]] = f["field"] + "_b"
            if "normalized" in f:
                rename_dict[f["normalized"]] = f["normalized"] + "_b"

        candidates_pdf = candidates_pdf.rename(columns=rename_dict)

        columns_a = [f.get("normalized", f["field"]) + "_a" for f in matching_fields]
        columns_b = [f.get("normalized", f["field"]) + "_b" for f in matching_fields]
        weights = [f["weight"] for f in matching_fields]

        def compute_distance(row) -> float:
            score = 0.0
            for column_a, column_b, weight in zip(columns_a, columns_b, weights):
                s1 = getattr(row, column_a)
                s2 = getattr(row, column_b)
                score += damerauLevenshtein(s1, s2, similarity=True) * weight
            return score

        candidates_pdf["score"] = candidates_pdf.apply(compute_distance, axis=1)
        matches_pdf = candidates_pdf[(candidates_pdf["score"] >= match_threshold)]
        matches_list.append(matches_pdf)
    all_matches_pdf = pd.concat(matches_list, axis=0)
    all_matches_pdf.to_csv(f"/tmp/matches_{f_index}")
    logger.info(f"Result of matching is saved to file /tmp/matches_{f_index}")


def find_matches(
    account_pdf: DataFrame,
    matching_fields: List[Dict[str, Any]],
    match_threshold: float,
    workers: int = 8,
    batch_size: int = 20_000
) -> None:
    """
        This function reads a CSV file containing pairs of ids (id_a, id_b) and finds matches between them by
        comparing the values of certain fields specified in matching_fields, using the Damerau-Levenshtein
        distance algorithm. The matching score is calculated as a weighted sum of the similarities of the field values
        between the pairs, and pairs with a score greater than or equal to match_threshold are considered matches.
        The matched pairs are then saved to a file in the tmp directory.
    """

    indexed_account_pdf = account_pdf.set_index("id")
    files = glob.glob("/tmp/candidates_*")
    logger.info(f"Finding matches started. Processing {len(files)} files with {workers} workers")
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                __find_matches,
                indexed_account_pdf,
                f_index,
                candidates_file,
                matching_fields,
                match_threshold,
                batch_size,
            )
            for f_index, candidates_file in enumerate(files)
        ]
        concurrent.futures.wait(futures)
        for future in futures:
            if future.exception() is not None:
                raise Exception(f"Error in finding matches: {future.exception()}")