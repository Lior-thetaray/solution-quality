import pickle
import concurrent.futures

import pandas as pd
from datasketch import MinHash, LeanMinHash
from nltk import ngrams

from thetaray.common.logging import logger


def __compute_minhashes(
    f_index: int,
    df: pd.DataFrame,
    number_of_permutation: int,
    minhash_lsh_matching_field: str,
    minhash_lsh_ngrams: int,
) -> None:
    logger.info(f"Start computing minhashes for chunk {f_index}")
    with open(f"/tmp/minhashes_{f_index}", "wb") as f:
        minhash = MinHash(num_perm=number_of_permutation)
        for row in df.itertuples(index=False):
            row_ngrams = ngrams(f" {getattr(row, minhash_lsh_matching_field)} ", minhash_lsh_ngrams)
            minhash.update_batch(["".join(d).encode("utf-8") for d in row_ngrams])
            lmh = LeanMinHash(minhash)
            buf = bytearray(lmh.bytesize())
            lmh.serialize(buf)
            pickle.dump((row.id, buf), f)
            minhash.clear()

    logger.info(f"Computing minhashes for chunk {f_index} is done. Output saved to /tmp/minhashes_{f_index}")

    
def compute_minhashes(
    account_pdf: pd.DataFrame,
    number_of_permutation: int = 64,
    minhash_lsh_matching_field: str = "normalized_name",
    minhash_lsh_ngrams: int = 2,
    workers: int = 8,
    chunk_size: int = 50_000
) -> None:
    """
        Computes MinHash LSH signatures for given account dataframe.
        MinHash LSH is a technique for approximating the Jaccard similarity between sets of items,
        by creating a signature (minhash) for each set, and then comparing the minhashes.
        This function computes minhashes for the given account dataframe by breaking it into chunks
        of a specified size and computing minhashes in parallel using multiple worker processes.
        The resulting minhashes are saved to /tmp/minhashes_* files.
    """
    chunks = [account_pdf[i:i + chunk_size] for i in range(0, account_pdf.shape[0], chunk_size)]
    logger.info(f"Started computing minhashes for {len(chunks)} chunks with size {chunk_size} each")
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                __compute_minhashes,
                f_index,
                pdf,
                number_of_permutation,
                minhash_lsh_matching_field,
                minhash_lsh_ngrams,
            )
            for f_index, pdf in enumerate(chunks)
        ]
        concurrent.futures.wait(futures)
        for future in futures:
            if future.exception() is not None:
                raise Exception(f"Exception occurred while computing minhashes: {future.exception()}")
        
    logger.info(f"Finished computing minhashes")

