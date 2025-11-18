import builtins as b
import statistics as st

import numpy as np
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql import Column

from common.libs.config.loader import load_config


tr_levenshtein_conf = load_config('libs/tr_levenshtein.yaml', domain='common')


def get_lev_ind(col1: str, col2: str, threshold: int = None) -> Column:
    """Compute the levenshtein distance between 2 columns

    Parameters
    ----------
    col1: str
        First column name
    col2: str
        Second column name
    threshold: int
        If the levenshtein distance is smaller than the threshold return boolean pyspark column equals to True, otherwise False. Defaults to 1.

    Returns
    -------
    Column
        Boolean column equals to True/False based on the levenshtein distance and the threshold
    """
    threshold = threshold if threshold is not None else tr_levenshtein_conf['threshold']
    col1_clean_array = _get_clean_array(col1)
    col2_clean_array = _get_clean_array(col2)
    new_lev_col = _new_lev_calc(col1_clean_array, col2_clean_array)
    basic_lev_col = levenshtein(col(col1), col(col2))
    final_lev_dist_col = least(new_lev_col, basic_lev_col)
    lev_ind_col = when(final_lev_dist_col < threshold, True).otherwise(False)
    return lev_ind_col


def _get_clean_array(col):
    punc = r'[!"#$%&\(\)*\+,-./:;<=>\?@\[\\\]^_\{\|\}~]'

    # REMOVE PUNCTUATION
    col_no_punc = lower(regexp_replace(col, punc, " "))

    # PREP FOR REMOVING 1-3 LETTER WORDS
    col_prep = regexp_replace(col_no_punc, ' ', "  ")
    col_prep = concat(lit(" "), col_prep, lit(" "))

    # REMOVING 1-3 LETTER WORDS AND UNWANTED SPACES
    col_clean = trim(regexp_replace(col_prep, " [^ ]{1,3} ", " "))

    col_clean_array = split(col_clean, " +")
    return col_clean_array

@udf(returnType=DoubleType())
def _new_lev_calc(arr1, arr2):
    
    def lev_distance(s, t):
        """ lev_distance:
            Calculates levenshtein distance between two strings.
        """
        # Initialize matrix of zeros
        rows = len(s)+1
        cols = len(t)+1
        distance = np.zeros((rows,cols),dtype = int)

        # Populate matrix of zeros with the indeces of each character of both strings
        for i in range(1, rows):
            for k in range(1, cols):
                distance[i][0] = i
                distance[0][k] = k

        # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions
        for col in range(1, cols):
            for row in range(1, rows):
                if s[row-1] == t[col-1]:
                    cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
                else:
                    cost = 1
                distance[row][col] = b.min(distance[row-1][col] + 1,      # Cost of deletions
                                           distance[row][col-1] + 1,          # Cost of insertions
                                           distance[row-1][col-1] + cost)     # Cost of substitutions

        # This is the minimum number of edits needed to convert string s to string t
        return distance[rows-1][cols-1]
    if (arr1 is None or arr1==[] or ((len(arr1)==1) and (arr1==['']))) or (arr2 is None or arr2==[] or ((len(arr2)==1) and (arr2==['']))) :
        res = float(100986000)
        return res
    else:
        arr_short = arr1 if len(arr1) <= len(arr2) else arr2
        arr_long = arr1 if len(arr1) > len(arr2) else arr2
        min_list = []
        for i in range(len(arr_short)):
            dist_list = []
            for j in range(len(arr_long)):
                dist_list.append(lev_distance(arr_short[i], arr_long[j]))
            min_list.append(b.min(dist_list))
        if min_list == []:
            res = float(100000)  # To signify the names don't match at all
        else:
            res = float(st.mean(min_list))

        return res