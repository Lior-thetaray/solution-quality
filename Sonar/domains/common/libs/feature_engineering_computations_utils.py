from pyspark.sql import Column, functions as f, DataFrame


def no_value_for_col(col_name) -> Column:
    return f.col(col_name).isNull() | f.isnan(col_name) | f.trim(f.lower(col_name)).isin(['', 'none', 'null', 'unknown', 'nil'])


def enrich_trx_with_keywords(trx_df, keywords_df) -> DataFrame: 
    keywords_df = keywords_df.groupBy("keyword_group").agg(f.concat_ws(",", f.collect_set("keyword")).alias('keyword_list'))
    keywords_dict = {row['keyword_group'].lower(): row['keyword_list'].split(",") for row in keywords_df.collect()}
    
    for keyword_group, keyword_list in keywords_dict.items():
        regex_string = r"(?i)(\b)(" + "|".join(keyword_list) + r")(\b)"
        trx_df = trx_df.withColumn(f"{keyword_group}_risky_keyword", f.regexp_extract('trx_description', regex_string, 0)).replace("", None, subset=[f"{keyword_group}_risky_keyword"])
    print("Risky keywords of the following groups were added:\n", [f"{keyword_group}_risky_keyword" for keyword_group in keywords_dict])

    for keyword_group in keywords_dict:
        trx_df = trx_df.withColumn(f"is_{keyword_group}_kw_found", f.col(f"{keyword_group}_risky_keyword").isNotNull())
    return trx_df
