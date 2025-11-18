"""
Alert Analysis Tools for CrewAI
Advanced CSV analysis tools for alert validation with LLM-driven insights
"""

from crewai.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
import pandas as pd
from pathlib import Path
import json


class JoinDatasetsInput(BaseModel):
    """Input schema for JoinDatasetsTool"""
    left_file: str = Field(..., description="Name of the left CSV file (e.g., 'tr_alert_table.csv')")
    right_file: str = Field(..., description="Name of the right CSV file (e.g., 'activity_risk_table.csv')")
    left_key: str = Field(..., description="Column name in left file to join on (e.g., 'id', 'tr_id')")
    right_key: str = Field(..., description="Column name in right file to join on (e.g., 'tr_id', 'alert_id')")
    join_type: str = Field(default="inner", description="Type of join: 'inner', 'left', 'right', 'outer'")


class JoinDatasetsTool(BaseTool):
    name: str = "Join CSV Datasets"
    description: str = """
    Joins two CSV datasets on specified keys and returns combined statistics.
    Useful for analyzing relationships between alerts, risks, and activities.
    Provides row counts before/after join, matching statistics, and sample joined data.
    """
    args_schema: Type[BaseModel] = JoinDatasetsInput
    
    def _run(self, left_file: str, right_file: str, left_key: str, right_key: str, join_type: str = "inner") -> str:
        """Join two CSV files and return statistics"""
        data_dir = Path("data")
        left_path = data_dir / left_file
        right_path = data_dir / right_file
        
        if not left_path.exists():
            return json.dumps({"error": f"Left file not found: {left_file}"})
        if not right_path.exists():
            return json.dumps({"error": f"Right file not found: {right_file}"})
        
        try:
            left_df = pd.read_csv(left_path)
            right_df = pd.read_csv(right_path)
            
            if left_key not in left_df.columns:
                return json.dumps({"error": f"Column '{left_key}' not found in {left_file}"})
            if right_key not in right_df.columns:
                return json.dumps({"error": f"Column '{right_key}' not found in {right_file}"})
            
            # Perform join
            joined_df = left_df.merge(
                right_df,
                left_on=left_key,
                right_on=right_key,
                how=join_type,
                suffixes=('_left', '_right')
            )
            
            # Calculate statistics
            left_unique = left_df[left_key].nunique()
            right_unique = right_df[right_key].nunique()
            joined_unique = joined_df[left_key].nunique()
            
            # Find unmatched records
            if join_type in ['left', 'outer']:
                left_unmatched = len(left_df[~left_df[left_key].isin(right_df[right_key])])
            else:
                left_unmatched = 0
            
            if join_type in ['right', 'outer']:
                right_unmatched = len(right_df[~right_df[right_key].isin(left_df[left_key])])
            else:
                right_unmatched = 0
            
            result = {
                "join_summary": {
                    "left_file": left_file,
                    "right_file": right_file,
                    "join_type": join_type,
                    "left_key": left_key,
                    "right_key": right_key
                },
                "row_counts": {
                    "left_rows": len(left_df),
                    "right_rows": len(right_df),
                    "joined_rows": len(joined_df),
                    "left_unique_keys": int(left_unique),
                    "right_unique_keys": int(right_unique),
                    "joined_unique_keys": int(joined_unique)
                },
                "match_statistics": {
                    "left_unmatched": int(left_unmatched),
                    "right_unmatched": int(right_unmatched),
                    "match_rate_left": round((1 - left_unmatched/len(left_df)) * 100, 2) if len(left_df) > 0 else 0,
                    "match_rate_right": round((1 - right_unmatched/len(right_df)) * 100, 2) if len(right_df) > 0 else 0
                },
                "joined_columns": list(joined_df.columns),
                "sample_joined_data": joined_df.head(5).to_dict(orient='records')
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({"error": f"Join failed: {str(e)}"})


class AggregateDatasetInput(BaseModel):
    """Input schema for AggregateDatasetTool"""
    filename: str = Field(..., description="Name of the CSV file to aggregate (e.g., 'evaluated_activities.csv')")
    group_by: List[str] = Field(..., description="List of column names to group by (e.g., ['year_month'], ['customer_id'])")
    agg_columns: Optional[List[str]] = Field(default=None, description="Optional: specific columns to aggregate (default: all numeric columns)")
    agg_functions: List[str] = Field(default=["count", "mean", "sum"], description="Aggregation functions: 'count', 'mean', 'sum', 'min', 'max', 'std'")


class AggregateDatasetTool(BaseTool):
    name: str = "Aggregate CSV Dataset"
    description: str = """
    Aggregates CSV data by specified columns and returns summary statistics.
    Useful for analyzing distributions, trends, and patterns in the data.
    Can calculate counts, means, sums, min/max, and standard deviations.
    """
    args_schema: Type[BaseModel] = AggregateDatasetInput
    
    def _run(self, filename: str, group_by: List[str], agg_columns: Optional[List[str]] = None, 
             agg_functions: List[str] = ["count", "mean", "sum"]) -> str:
        """Aggregate CSV data by columns"""
        data_dir = Path("data")
        file_path = data_dir / filename
        
        if not file_path.exists():
            return json.dumps({"error": f"File not found: {filename}"})
        
        try:
            df = pd.read_csv(file_path)
            
            # Validate group_by columns
            missing_cols = [col for col in group_by if col not in df.columns]
            if missing_cols:
                return json.dumps({"error": f"Columns not found: {missing_cols}"})
            
            # Select columns to aggregate
            if agg_columns:
                missing_agg = [col for col in agg_columns if col not in df.columns]
                if missing_agg:
                    return json.dumps({"error": f"Aggregation columns not found: {missing_agg}"})
                numeric_cols = agg_columns
            else:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            # Remove group_by columns from aggregation if present
            numeric_cols = [col for col in numeric_cols if col not in group_by]
            
            if not numeric_cols:
                return json.dumps({"error": "No numeric columns found for aggregation"})
            
            # Perform aggregation
            agg_dict = {col: agg_functions for col in numeric_cols}
            grouped = df.groupby(group_by).agg(agg_dict)
            
            # Flatten multi-level columns
            grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
            grouped = grouped.reset_index()
            
            result = {
                "aggregation_summary": {
                    "filename": filename,
                    "group_by_columns": group_by,
                    "aggregated_columns": numeric_cols,
                    "functions_applied": agg_functions,
                    "total_groups": len(grouped)
                },
                "group_statistics": {
                    "total_rows_before": len(df),
                    "unique_groups": int(df.groupby(group_by).ngroups),
                    "avg_rows_per_group": round(len(df) / df.groupby(group_by).ngroups, 2) if df.groupby(group_by).ngroups > 0 else 0
                },
                "aggregated_data": grouped.to_dict(orient='records')[:50]  # Limit to 50 groups
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({"error": f"Aggregation failed: {str(e)}"})


class CrossTableAnalysisInput(BaseModel):
    """Input schema for CrossTableAnalysisTool"""
    files: List[str] = Field(..., description="List of CSV files to analyze (e.g., ['tr_alert_table.csv', 'activity_risk_table.csv', 'evaluated_activities.csv'])")
    key_column: str = Field(..., description="Common key column across files (e.g., 'tr_id', 'id')")


class CrossTableAnalysisTool(BaseTool):
    name: str = "Cross-Table Analysis"
    description: str = """
    Analyzes relationships across multiple CSV files using a common key.
    Identifies orphan records, coverage gaps, and data consistency issues.
    Provides comprehensive statistics about how tables relate to each other.
    Perfect for validating data integrity across alerts, risks, and activities.
    """
    args_schema: Type[BaseModel] = CrossTableAnalysisInput
    
    def _run(self, files: List[str], key_column: str) -> str:
        """Analyze cross-table relationships"""
        data_dir = Path("data")
        
        try:
            # Load all files
            dataframes = {}
            for filename in files:
                file_path = data_dir / filename
                if not file_path.exists():
                    return json.dumps({"error": f"File not found: {filename}"})
                
                df = pd.read_csv(file_path)
                if key_column not in df.columns:
                    return json.dumps({"error": f"Column '{key_column}' not found in {filename}"})
                
                dataframes[filename] = df
            
            # Get unique keys from each file
            key_sets = {}
            for filename, df in dataframes.items():
                key_sets[filename] = set(df[key_column].unique())
            
            # Calculate overlaps
            all_keys = set().union(*key_sets.values())
            
            # Find orphans (keys missing from other tables)
            orphans = {}
            for filename, keys in key_sets.items():
                other_files = [f for f in files if f != filename]
                for other_file in other_files:
                    missing_in_other = keys - key_sets[other_file]
                    if missing_in_other:
                        orphans[f"{filename}_missing_in_{other_file}"] = {
                            "count": len(missing_in_other),
                            "sample_keys": list(missing_in_other)[:10]
                        }
            
            # Calculate coverage matrix
            coverage_matrix = {}
            for file1 in files:
                coverage_matrix[file1] = {}
                for file2 in files:
                    if file1 != file2:
                        overlap = len(key_sets[file1] & key_sets[file2])
                        total = len(key_sets[file1])
                        coverage_pct = round((overlap / total * 100), 2) if total > 0 else 0
                        coverage_matrix[file1][file2] = {
                            "overlap_count": overlap,
                            "coverage_percent": coverage_pct
                        }
            
            result = {
                "analysis_summary": {
                    "files_analyzed": files,
                    "key_column": key_column,
                    "total_unique_keys": len(all_keys)
                },
                "file_statistics": {
                    filename: {
                        "total_rows": len(df),
                        "unique_keys": len(keys),
                        "duplicate_keys": len(df) - len(keys)
                    }
                    for filename, (df, keys) in zip(files, [(dataframes[f], key_sets[f]) for f in files])
                },
                "coverage_matrix": coverage_matrix,
                "orphan_records": orphans,
                "data_quality_status": "PASS" if not orphans else "FAIL - Orphan records detected"
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({"error": f"Cross-table analysis failed: {str(e)}"})
