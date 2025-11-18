"""
Parameters:
matching_fields_parameters: List of matching fields and their
weight to use for matching.
    Each element in the list is a dictionary that has the following keys:
    - "field": name of the field to use for matching
    - "weight": weight to give this field when computing the final match score
    - "normalized": (optional) normalized name of the field that will be used for matching instead not normalized field
minhash_lsh_chunk_size (int) - Number of records that will be processed by one worker for computing minshash lsh.
minhash_lsh_matching_field (str): The name of the field to use for minhash LSH indexing and querying.
minhash_lsh_num_permutations (int): The number of permutations to use in the minhash LSH.
    Higher number of permutations will increase the accuracy of the LSH but will also increase the computational cost.
minhash_lsh_jaccard_threshold (float): The Jaccard similarity threshold to use for querying the minhash LSH.
    Lower threshold will increase the number of candidates but also increase the number of false positives.
minhash_lsh_ngrams (int): The number of grams to use for minhash LSH indexing.
    The number of grams used will affect the granularity of the indexing and thus the
    recall and precision of the LSH.
match_threshold (float): The threshold to use when determining if two accounts match.
match_batch_size (int): The batch size for calculating matching score by Damerau-Levenshtein algorithm.
workers (int): The number of worker processes to use for parallel computation.
auto_confirmation_threshold(float | int): the match_threshold after which we apply auto confirmed state to matching
    entities, -1 - disabled
"""

matching_fields_parameters = [
    {
        "field": "NM",
        "normalized": "normalized_name",
        "weight": 0.5,
    },
    {
        "field": "AD",
        "weight": 0.5,
    },
]
minhash_lsh_matching_field: str = "normalized_name"
minhash_lsh_chunk_size: int = 50_000
minhash_lsh_num_permutations: int = 64
minhash_lsh_jaccard_threshold: float = 0.8
minhash_lsh_ngrams: int = 2
match_threshold: float = 0.8
match_batch_size: int = 20_000
workers: int = 8

auto_confirmation_threshold = 0.8  # -1 to disable
