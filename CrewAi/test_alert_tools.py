"""
Test Alert Analysis Tools
Demonstrates the new CSV analysis tools for LLM-driven validation
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from tools.csv_tools import CSVListTool, CSVDatasetReaderTool
from tools.alert_analysis_tools import JoinDatasetsTool, AggregateDatasetTool, CrossTableAnalysisTool
import json


def print_section(title):
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_list_csvs():
    print_section("1. LIST CSV FILES")
    tool = CSVListTool()
    result = tool._run()
    data = json.loads(result)
    print(json.dumps(data, indent=2))


def test_read_csv():
    print_section("2. READ CSV DATASET")
    tool = CSVDatasetReaderTool()
    result = tool._run(filename="tr_alert_table.csv", limit=3)
    data = json.loads(result)
    
    # Print summary (not full data)
    print(f"Filename: {data.get('filename')}")
    print(f"Total Rows: {data.get('total_rows')}")
    print(f"Total Columns: {data.get('total_columns')}")
    print(f"Columns: {data.get('columns')[:10]}...")  # First 10 columns
    print(f"Sample Data: {len(data.get('sample_data', []))} rows")


def test_join_datasets():
    print_section("3. JOIN DATASETS (Alerts + Risks)")
    tool = JoinDatasetsTool()
    result = tool._run(
        left_file="tr_alert_table.csv",
        right_file="activity_risk_table.csv",
        left_key="id",  # Assuming alerts have 'id' column
        right_key="tr_id",
        join_type="left"
    )
    data = json.loads(result)
    print(json.dumps(data.get('join_summary'), indent=2))
    print(json.dumps(data.get('row_counts'), indent=2))
    print(json.dumps(data.get('match_statistics'), indent=2))


def test_aggregate():
    print_section("4. AGGREGATE DATASET (Activities by Month)")
    tool = AggregateDatasetTool()
    result = tool._run(
        filename="evaluated_activities.csv",
        group_by=["year_month"],
        agg_functions=["count", "mean", "sum"]
    )
    data = json.loads(result)
    print(json.dumps(data.get('aggregation_summary'), indent=2))
    print(json.dumps(data.get('group_statistics'), indent=2))
    print(f"Sample aggregated data (first 5):")
    for row in data.get('aggregated_data', [])[:5]:
        print(f"  {row}")


def test_cross_table():
    print_section("5. CROSS-TABLE ANALYSIS (All 3 Files)")
    tool = CrossTableAnalysisTool()
    result = tool._run(
        files=[
            "tr_alert_table.csv",
            "activity_risk_table.csv",
            "evaluated_activities.csv"
        ],
        key_column="tr_id"  # Common key
    )
    data = json.loads(result)
    print(json.dumps(data, indent=2))


def main():
    print("\n" + "🔍 TESTING ALERT ANALYSIS TOOLS".center(60, "="))
    
    try:
        test_list_csvs()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    try:
        test_read_csv()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    try:
        test_join_datasets()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    try:
        test_aggregate()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    try:
        test_cross_table()
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "✅ TESTING COMPLETE".center(60, "=") + "\n")


if __name__ == "__main__":
    main()
