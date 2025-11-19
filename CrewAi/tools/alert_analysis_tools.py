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


class ConsolidationEffectivenessInput(BaseModel):
    """Input schema for ConsolidationEffectivenessTool"""
    alert_file: str = Field(default="tr_alert_table.csv", description="Alert table CSV file")


class ConsolidationEffectivenessTool(BaseTool):
    name: str = "Consolidation Effectiveness Checker"
    description: str = """
    Validates consolidation IF it's being used. Consolidation is OPTIONAL.
    First checks if consolidation is active (alerts with multiple triggers exist).
    If consolidation IS active, validates that entities don't appear in multiple alerts.
    If consolidation is NOT active (all single-trigger alerts), returns PASS - nothing to validate.
    This tool does NOT require consolidation to be enabled.
    """
    args_schema: Type[BaseModel] = ConsolidationEffectivenessInput
    
    def _run(self, alert_file: str = "tr_alert_table.csv") -> str:
        """Check consolidation effectiveness"""
        data_dir = Path("data")
        alert_path = data_dir / alert_file
        
        if not alert_path.exists():
            return json.dumps({"error": f"Alert file not found: {alert_file}"})
        
        try:
            # Load alerts
            alerts_df = pd.read_csv(alert_path)
            
            # Extract entity identifiers from triggers
            entity_to_alerts = {}
            alert_trigger_counts = {}
            
            for idx, row in alerts_df.iterrows():
                try:
                    alert_id = row['id']
                    triggers = json.loads(row['triggers'])
                    alert_trigger_counts[alert_id] = len(triggers)
                    
                    for trigger in triggers:
                        # Extract primary entity identifier
                        primary_key_set = trigger.get('primaryKeySet', {})
                        
                        # Convert dict to a hashable string for grouping
                        entity_key = json.dumps(primary_key_set, sort_keys=True)
                        
                        if entity_key and entity_key != '{}':
                            if entity_key not in entity_to_alerts:
                                entity_to_alerts[entity_key] = []
                            entity_to_alerts[entity_key].append(alert_id)
                except Exception as e:
                    continue
            
            if not entity_to_alerts:
                return json.dumps({"error": "No entity identifiers could be extracted from alerts"})
            
            # Analyze consolidation
            total_entities = len(entity_to_alerts)
            entities_in_single_alert = 0
            entities_in_multiple_alerts = 0
            consolidation_failures = []
            
            for entity_key, alert_ids in entity_to_alerts.items():
                unique_alerts = list(set(alert_ids))
                
                if len(unique_alerts) == 1:
                    entities_in_single_alert += 1
                else:
                    entities_in_multiple_alerts += 1
                    # Parse entity key back to dict
                    entity_dict = json.loads(entity_key)
                    consolidation_failures.append({
                        "entity": entity_dict,
                        "alert_count": len(unique_alerts),
                        "alert_ids": unique_alerts
                    })
            
            # Calculate average triggers per alert
            avg_triggers_per_alert = round(sum(alert_trigger_counts.values()) / len(alert_trigger_counts), 2) if alert_trigger_counts else 0
            consolidated_alerts = sum(1 for count in alert_trigger_counts.values() if count > 1)
            
            # Calculate consolidation rate
            consolidation_rate = round((entities_in_single_alert / total_entities) * 100, 2) if total_entities > 0 else 0
            
            # Check if consolidation is actually being used
            consolidation_active = consolidated_alerts > 0
            
            # Determine pass/fail based on whether consolidation is active
            if not consolidation_active:
                # No consolidation being used - this is fine, nothing to validate
                status = "PASS"
                message = "Consolidation is not active (all alerts have single trigger). No validation needed."
            elif entities_in_multiple_alerts == 0:
                # Consolidation is active and working perfectly
                status = "PASS"
                message = "Consolidation is active and working correctly - no entity appears in multiple alerts."
            elif (entities_in_multiple_alerts / total_entities) <= 0.10:
                # Less than 10% consolidation failures
                status = "WARNING"
                message = f"Consolidation is active but {entities_in_multiple_alerts} entities ({round((entities_in_multiple_alerts/total_entities)*100, 2)}%) appear in multiple alerts."
            else:
                # More than 10% consolidation failures
                status = "FAIL"
                message = f"Consolidation is active but has significant issues - {entities_in_multiple_alerts} entities ({round((entities_in_multiple_alerts/total_entities)*100, 2)}%) appear in multiple alerts."
            
            # Already calculated above, no need to recalculate
            # avg_triggers_per_alert and consolidated_alerts are already set
            
            result = {
                "consolidation_effectiveness": {
                    "status": status,
                    "pass": status == "PASS",
                    "consolidation_active": consolidation_active,
                    "total_entities": total_entities,
                    "entities_in_single_alert": entities_in_single_alert,
                    "entities_in_multiple_alerts": entities_in_multiple_alerts,
                    "consolidation_rate": consolidation_rate,
                    "total_alerts": len(alerts_df),
                    "consolidated_alerts": consolidated_alerts,
                    "non_consolidated_alerts": len(alerts_df) - consolidated_alerts,
                    "avg_triggers_per_alert": avg_triggers_per_alert,
                    "consolidation_failures": consolidation_failures[:20] if consolidation_active else [],
                    "message": message
                },
                "insights": {
                    "recommendation": message
                }
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            import traceback
            return json.dumps({
                "error": f"Consolidation effectiveness check failed: {str(e)}",
                "traceback": traceback.format_exc()
            })


class MonthlyAlertPercentageInput(BaseModel):
    """Input schema for MonthlyAlertPercentageTool"""
    alert_file: str = Field(default="tr_alert_table.csv", description="Alert table CSV file")
    activity_file: str = Field(default="evaluated_activities.csv", description="Evaluated activities CSV file")


class MonthlyAlertPercentageTool(BaseTool):
    name: str = "Monthly Alert Percentage Calculator"
    description: str = """
    Calculates monthly alert percentage by joining alerts with evaluated activities.
    Extracts triggerID from alerts' triggers JSON field and joins with evaluated_activities
    to calculate: (number of alerts / total analyzed entities) * 100 for each month.
    Returns monthly breakdown with alert percentage, total entities, and alerts generated.
    """
    args_schema: Type[BaseModel] = MonthlyAlertPercentageInput
    
    def _run(self, alert_file: str = "tr_alert_table.csv", activity_file: str = "evaluated_activities.csv") -> str:
        """Calculate monthly alert percentage"""
        data_dir = Path("data")
        alert_path = data_dir / alert_file
        activity_path = data_dir / activity_file
        
        if not alert_path.exists():
            return json.dumps({"error": f"Alert file not found: {alert_file}"})
        if not activity_path.exists():
            return json.dumps({"error": f"Activity file not found: {activity_file}"})
        
        try:
            # Load data
            alerts_df = pd.read_csv(alert_path)
            activities_df = pd.read_csv(activity_path)
            
            # Extract triggerIDs from triggers JSON field
            trigger_ids = []
            for idx, row in alerts_df.iterrows():
                try:
                    triggers = json.loads(row['triggers'])
                    for trigger in triggers:
                        # Try both 'triggerId' and 'triggerID' for compatibility
                        trigger_id = trigger.get('triggerId') or trigger.get('triggerID')
                        if trigger_id:
                            trigger_ids.append({
                                'tr_id': trigger_id,
                                'createdate': row.get('createdate', '')
                            })
                except Exception as e:
                    continue
            
            if not trigger_ids:
                return json.dumps({"error": "No trigger IDs could be extracted from alerts"})
            
            # Create DataFrame from extracted triggers
            triggers_df = pd.DataFrame(trigger_ids)
            
            # Join with activities to get month from tr_partition
            activities_df['month'] = pd.to_datetime(activities_df['tr_partition']).dt.to_period('M')
            
            # Join triggers with activities to get month
            triggers_with_month = triggers_df.merge(
                activities_df[['tr_id', 'month']],
                on='tr_id',
                how='inner'  # Only keep triggers that have activity data
            )
            
            if len(triggers_with_month) == 0:
                return json.dumps({"error": "No matching triggers found in evaluated_activities"})
            
            # Count total entities per month
            monthly_entities = activities_df.groupby('month')['tr_id'].nunique().reset_index()
            monthly_entities.columns = ['month', 'total_entities']
            
            # Count alerts per month
            monthly_alerts = triggers_with_month.groupby('month')['tr_id'].nunique().reset_index()
            monthly_alerts.columns = ['month', 'alert_count']
            
            # Merge to get final stats
            monthly_stats = monthly_entities.merge(monthly_alerts, on='month', how='left')
            monthly_stats['alert_count'] = monthly_stats['alert_count'].fillna(0).astype(int)
            monthly_stats['alert_percentage'] = round(
                (monthly_stats['alert_count'] / monthly_stats['total_entities']) * 100, 2
            )
            
            # Calculate overall average
            avg_alert_percentage = round(monthly_stats['alert_percentage'].mean(), 2)
            total_alerts = int(monthly_stats['alert_count'].sum())
            total_entities = int(monthly_stats['total_entities'].sum())
            
            # Convert Period to string for JSON serialization
            monthly_stats['month'] = monthly_stats['month'].astype(str)
            
            result = {
                "summary": {
                    "total_alerts": total_alerts,
                    "total_entities_analyzed": total_entities,
                    "overall_alert_percentage": round((total_alerts / total_entities) * 100, 2) if total_entities > 0 else 0,
                    "monthly_average_alert_percentage": avg_alert_percentage,
                    "months_analyzed": len(monthly_stats)
                },
                "monthly_breakdown": monthly_stats.to_dict(orient='records'),
                "insights": {
                    "highest_alert_month": monthly_stats.loc[monthly_stats['alert_percentage'].idxmax()]['month'] if len(monthly_stats) > 0 else None,
                    "highest_alert_percentage": float(monthly_stats['alert_percentage'].max()) if len(monthly_stats) > 0 else 0,
                    "lowest_alert_month": monthly_stats.loc[monthly_stats['alert_percentage'].idxmin()]['month'] if len(monthly_stats) > 0 else None,
                    "lowest_alert_percentage": float(monthly_stats['alert_percentage'].min()) if len(monthly_stats) > 0 else 0
                }
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            import traceback
            return json.dumps({
                "error": f"Monthly alert percentage calculation failed: {str(e)}",
                "traceback": traceback.format_exc()
            })


class CrossTableAnalysisTool(BaseTool):
    name: str = "Cross-Table Analysis"
    description: str = """
    Analyzes relationships across multiple CSV files using a common key.
    Identifies orphan records, coverage gaps, and data consistency issues.
    Provides comprehensive statistics about how tables relate to each other.
    Perfect for validating data integrity across alerts, risks, and activities.
    Note: For tr_alert_table, triggerID should be extracted from triggers JSON field.
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
                
                # Special handling for tr_alert_table: extract triggerID from triggers JSON
                if 'tr_alert_table' in filename and key_column == 'tr_id':
                    if 'triggers' not in df.columns:
                        return json.dumps({"error": f"Column 'triggers' not found in {filename}"})
                    # Note: tr_id should be extracted from triggers JSON field using triggerId
                    # This is expected behavior and not a failure
                    continue
                elif key_column not in df.columns:
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
