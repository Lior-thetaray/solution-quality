#!/usr/bin/env python3
"""Test CSV dataset reader tools."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.csv_tools import CSVDatasetReaderTool, CSVListTool
import json

def test_csv_tools():
    """Test CSV reading tools."""
    
    print("=" * 80)
    print("CSV Dataset Tools Test")
    print("=" * 80)
    
    # Test 1: List available CSV files
    print("\n1. Listing available CSV files...")
    list_tool = CSVListTool()
    result = list_tool._run()
    data = json.loads(result)
    
    if data.get("status") == "success":
        print(f"✅ Found {data['total_files']} CSV file(s) in: {data['data_directory']}")
        if data['files']:
            for file in data['files']:
                print(f"   - {file['filename']} ({file['size']})")
        else:
            print("   📁 No CSV files found yet. Add CSV files to the data/ directory.")
    else:
        print(f"❌ Error: {data.get('error')}")
        return False
    
    # Test 2: Try to read a CSV file (if available)
    if data.get('files'):
        print(f"\n2. Reading first CSV file: {data['files'][0]['filename']}...")
        reader_tool = CSVDatasetReaderTool()
        result = reader_tool._run(filename=data['files'][0]['filename'], limit=5)
        csv_data = json.loads(result)
        
        if csv_data.get("status") == "success":
            print("✅ CSV file read successfully!")
            stats = csv_data.get('statistics', {})
            print(f"   Total rows: {stats.get('total_rows')}")
            print(f"   Total columns: {stats.get('total_columns')}")
            print(f"   Columns: {', '.join(stats.get('columns', []))}")
            print(f"   Returned rows (limited to 5): {csv_data.get('rows_returned')}")
        else:
            print(f"❌ Error reading CSV: {csv_data.get('error')}")
    else:
        print("\n2. Skipping CSV read test (no files available)")
        print("   💡 To test: Add a CSV file to CrewAi/data/ and run again")
    
    print("\n" + "=" * 80)
    print("✅ CSV tools are ready!")
    print("📁 Add your dataset CSV files to: CrewAi/data/")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        test_csv_tools()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
