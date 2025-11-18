import glob
import pickle
import concurrent.futures
from typing import List

from datasketch import LeanMinHash, MinHashLSH

from thetaray.common.logging import logger


def __query_minhashes(lsh: MinHashLSH, f_index: int, mh_file: str) -> None:
    logger.info(f"Performing query on file {mh_file}")
    with open(f"/tmp/candidates_{f_index}", "w") as out:
        out.write("id_a,id_b\n")
        with open(mh_file, "rb") as f:
            while True:
                try:
                    id, serialized_lmh = pickle.load(f)
                    lmh = LeanMinHash.deserialize(serialized_lmh)
                    results = lsh.query(lmh)
                    if results:
                        for r in results:
                            if id != r:
                                out.write(f"{id},{r}\n")
                except EOFError:
                    break
    logger.info(f"Output saved to file /tmp/candidates_{f_index}")


def __load_lsh(lsh: MinHashLSH, files: List[str]) -> None:
    for mh_file in files:
        with open(mh_file, "rb") as f:
            while True:
                try:
                    id, serialized_lmh = pickle.load(f)
                    lmh = LeanMinHash.deserialize(serialized_lmh)
                    lsh.insert(id, lmh, check_duplication=False)
                except EOFError:
                    break


def collect_candidates(minhash_lsh_jaccard_threshold: float, minhash_lsh_num_permutations: int, workers: int) -> None:
    """
        This function performs a query on a MinHash LSH object using minhash files as input.
        MinHash LSH is a Locality Sensitive Hashing technique that is used to perform approximate near-duplicate
        detection. It uses MinHash signatures to quickly identify candidate pairs of similar items in large datasets.
        The function loads the minhash files into memory using the `__load_lsh` method,
        performs queries on the LSH structure using the `__query_minhashes` method in parallel,
    """
    files = glob.glob("/tmp/minhashes_*")
    lsh = MinHashLSH(threshold=minhash_lsh_jaccard_threshold, num_perm=minhash_lsh_num_permutations)
    # Phase 1
    logger.info("Loading persisted MinHashes into in memory LSH structure")
    __load_lsh(lsh, files)

    # Phase 2
    # (multiprocessing is using fork, so LSH is accessible to all child processes)
    logger.info(f"Performing parallel queries over the LHS structure from {len(files)} file in {workers} processes")
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(__query_minhashes, lsh, f_index, mh_file) for f_index, mh_file in enumerate(files)]
        concurrent.futures.wait(futures)
        for future in futures:
            if future.exception() is not None:
                raise f"Exception occurred during collecting candidates: {future.exception()}"
