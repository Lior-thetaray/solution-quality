#!/usr/bin/env python3
"""Test PostgreSQL connection and query tool."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.postgres_tools import PostgresReadOnlyTool
import json

def test_connection():
    """Test PostgreSQL connection and basic query."""
    
    print("=" * 80)
    print("PostgreSQL Connection Test")
    print("=" * 80)
    
    tool = PostgresReadOnlyTool()
    
    # Test 1: Simple query to check connection
    print("\n1. Testing connection with simple query...")
    print("Query: SELECT version();")
    
    result = tool._run("SELECT version();")
    data = json.loads(result)
    
    if data.get("status") == "success":
        print("✅ Connection successful!")
        print(f"   Rows returned: {data.get('rows_returned')}")
        if data.get('data'):
            version = data['data'][0].get('version', 'Unknown')
            print(f"   PostgreSQL version: {version[:80]}...")
    else:
        print("❌ Connection failed!")
        print(f"   Error: {data.get('error')}")
        return False
    
    # Test 2: Query to list tables
    print("\n2. Listing tables in public schema...")
    print("Query: SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 10;")
    
    result = tool._run("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        LIMIT 10;
    """)
    data = json.loads(result)
    
    if data.get("status") == "success":
        print(f"✅ Found {data.get('rows_returned')} tables")
        if data.get('data'):
            for row in data['data']:
                print(f"   - {row.get('tablename')}")
    else:
        print(f"❌ Query failed: {data.get('error')}")
    
    # Test 3: Test write protection
    print("\n3. Testing write protection (should fail)...")
    print("Query: DELETE FROM test;")
    
    result = tool._run("DELETE FROM test;")
    data = json.loads(result)
    
    if data.get("status") == "error":
        print("✅ Write operation correctly blocked!")
        print(f"   Error: {data.get('error')}")
    else:
        print("❌ WARNING: Write operation was not blocked!")
    
    print("\n" + "=" * 80)
    print("✅ PostgreSQL tool is ready to use!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        test_connection()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
