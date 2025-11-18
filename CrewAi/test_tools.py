#!/usr/bin/env python3
"""Quick test script to verify tools are working."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.code_analysis_tools import (
    PythonFeatureAnalyzerTool,
    YAMLConfigAnalyzerTool,
    DatasetAnalyzerTool,
    DAGAnalyzerTool,
    NotebookAnalyzerTool
)

def test_tools():
    """Test each tool with demo_fuib domain."""
    domain = "demo_fuib"
    
    print(f"Testing tools with domain: {domain}\n")
    print("="*80)
    
    # Test Feature Analyzer
    print("\n1. Testing PythonFeatureAnalyzerTool...")
    feature_tool = PythonFeatureAnalyzerTool()
    result = feature_tool._run(domain=domain)
    print(f"Result preview: {result[:200]}...")
    
    # Test YAML Config Analyzer
    print("\n2. Testing YAMLConfigAnalyzerTool...")
    yaml_tool = YAMLConfigAnalyzerTool()
    result = yaml_tool._run(domain=domain)
    print(f"Result preview: {result[:200]}...")
    
    # Test Dataset Analyzer
    print("\n3. Testing DatasetAnalyzerTool...")
    dataset_tool = DatasetAnalyzerTool()
    result = dataset_tool._run(domain=domain)
    print(f"Result preview: {result[:200]}...")
    
    # Test DAG Analyzer
    print("\n4. Testing DAGAnalyzerTool...")
    dag_tool = DAGAnalyzerTool()
    result = dag_tool._run(domain=domain)
    print(f"Result preview: {result[:200]}...")
    
    # Test Notebook Analyzer
    print("\n5. Testing NotebookAnalyzerTool...")
    notebook_tool = NotebookAnalyzerTool()
    result = notebook_tool._run(domain=domain)
    print(f"Result preview: {result[:200]}...")
    
    print("\n" + "="*80)
    print("✅ All tools tested successfully!")

if __name__ == "__main__":
    test_tools()
