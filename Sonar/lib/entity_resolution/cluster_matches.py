import glob
import itertools
import uuid

import networkit as nk
import networkx as nx
import numpy as np
import pandas as pd

from thetaray.common.logging import logger


def cluster_matches(account_pdf: pd.DataFrame, previous_match_pdf: pd.DataFrame) -> pd.DataFrame:
    """
        This function reads in multiple files containing match information, concatenates them into a single
        DataFrame, and then finds all the cliques (i.e. fully connected subgraphs) in the graph
        formed from the matches. The function then filters cliques that have size more than 1, and
        computes summary statistics (mean) of the scores per clique. Finally, it
        merges the final DataFrame with the input account DataFrame, and writes the final
        DataFrame to a CSV file.
        Parameters:
            account_pdf (pd.DataFrame): Accounts input dataframe
            previous_match_pdf (pd.DataFrame): Previously found matches
    """
    try:
        files = glob.glob("/tmp/matches_*")
        files_count = len(files)
        logger.info(f"Reading {files_count} files with matches")

        if files_count == 0:
            return pd.DataFrame(
                columns=[*["source", "clique", "mean_score", "clique_size"], *account_pdf.columns[1:-1]]
            )

        df_list = list()
        read_kwargs = {}
        if pd.api.types.is_string_dtype(account_pdf["id"]):
            read_kwargs['dtype'] = {"id_a": str, 'id_b': str}

        for filename in files:
            df = pd.read_csv(filename, **read_kwargs)
            df_list.append(df)

        # Concatenate all the dataframes in df_list into one dataframe

        matches_pdf = pd.concat(df_list, axis=0, ignore_index=True)
        # Set the index of account_df as "id"
        indexed_account_pdf = account_pdf.set_index("id")

        # Create a NetworkX graph from the DataFrame of matches
        nxG = nx.from_pandas_edgelist(matches_pdf, source="id_a", target="id_b")
        G = nk.nxadapter.nx2nk(nxG)

        # Create a map of node id to node index
        idmap = dict((u, id) for (id, u) in zip(nxG.nodes(), range(nxG.number_of_nodes())))
        # Find all cliques in the graph
        cliques = nk.clique.MaximalCliques(G).run().getCliques()

        # Iterate through cliques and find all combination of pairs of nodes
        rows = list()
        for idx, c in enumerate(cliques):
            clique_id = str(uuid.uuid4())
            permutations = itertools.permutations(c, 2)
            for permutation in permutations:
                rows.append((clique_id, idmap[permutation[0]], idmap[permutation[1]]))

        # Create a DataFrame of clique information
        cliques_pdf = pd.DataFrame(rows, columns=["clique", "source", "target"])
        # Merge the clique DataFrame with the matches DataFrame
        cliques_pdf = pd.merge(cliques_pdf, matches_pdf, left_on=["source", "target"], right_on=["id_a", "id_b"])
        cliques_pdf = cliques_pdf.drop(["id_a", "id_b"], axis=1)
        cliques_pdf = cliques_pdf.sort_values(by=["clique", "source"])

        if not previous_match_pdf.empty:
            # aligh previous matches structure with new matches structure to concat them for recalculating party size
            previous_match_pdf = previous_match_pdf[["id", "source_node", "mean_score"]]
            previous_match_pdf = previous_match_pdf.rename(columns={"id": "source", "source_node": "clique"})

            # Selecting only newly matched account omitting account that was found as source before
            incr_matches = cliques_pdf[~cliques_pdf["source"].isin(previous_match_pdf["source"])]
            # Selecting accounts matched target has clique and source doesn't. In this case we're sure that this is new account matched to existing
            incr_matches = incr_matches[incr_matches.source_node_y.notna() & incr_matches.source_node_x.isna()]
            # Replacing generated clique with clique of already found party
            incr_matches["clique"] = incr_matches["source_node_y"]

            # Compute mean score per source and clique for incremented cliques
            incr_nodes_clique_distance = incr_matches.groupby(["source", "clique"], as_index=False).agg(
                {"score": {np.mean}}
            )
            incr_nodes_clique_distance.columns = ["source", "clique", "mean_score"]
            incr_matches = incr_nodes_clique_distance.loc[
                incr_nodes_clique_distance.groupby(["source"])["mean_score"].idxmax()]

            # Extend in memory graph with incremented cliques
            incremented_cliques = pd.concat([incr_matches, previous_match_pdf])
            del previous_match_pdf
            # Select rest of accounts that was matched beside of incremental matching
            cliques_pdf = cliques_pdf[~cliques_pdf["source"].isin(incremented_cliques["source"])]
        else:
            incremented_cliques = None

        # Compute mean score per source and clique for new cliques
        nodes_clique_distance = cliques_pdf.groupby(["source", "clique"], as_index=False).agg({"score": {np.mean}})
        nodes_clique_distance.columns = ["source", "clique", "mean_score"]
        new_cliques = nodes_clique_distance.loc[nodes_clique_distance.groupby(["source"])["mean_score"].idxmax()]

        # concat New cliques with incremented previous cliques
        if incremented_cliques is not None:
            matching_cliques = pd.concat([new_cliques, incremented_cliques])
        else:
            matching_cliques = new_cliques
        del new_cliques, incremented_cliques

        # Count the number of sources per clique
        rows_per_clique = matching_cliques.groupby(["clique"], as_index=False).agg({"source": ["count"]})
        rows_per_clique.columns = ["clique", "clique_size"]
        rows_per_clique.set_index("clique")

        # Retain only clique which have more than one element
        matching_cliques = pd.merge(matching_cliques, rows_per_clique, left_on="clique", right_on="clique")
        matching_cliques = matching_cliques[(matching_cliques["clique_size"] > 1)]

        # Merge the matching_cliques DataFrame with the input account DataFrame
        matching_cliques = pd.merge(matching_cliques, indexed_account_pdf, left_on="source", right_on="id")
        matching_cliques = matching_cliques.sort_values(by=["clique"])

        # Remove old values
        matching_cliques = matching_cliques[matching_cliques.source_node.isna()].drop("source_node", axis=1)

        matching_cliques.to_csv("/tmp/clustered_matches.csv")
        logger.info("Final output is returned and saved to file /tmp/clustered_matches.csv")
        return matching_cliques
    except Exception as e:
        raise Exception(f"Error occured during matches clustering: {e}")
