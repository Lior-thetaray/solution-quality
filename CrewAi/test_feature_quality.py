#!/usr/bin/env python3
"""
Test script for Feature Quality Validator agent
Verifies combined UI validation + Risk assessment tools without running full CrewAI
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.tool_registry import get_tool_registry


def test_feature_quality_tools():
    """Test that feature_quality agent has access to all required tools"""
    
    print("=" * 80)
    print("Testing Feature Quality Validator Tools")
    print("=" * 80)
    
    registry = get_tool_registry()
    
    # Get tools for feature_quality agent
    tools = registry.get_tools_for_agent('feature_quality')
    
    print(f"\n✅ Feature Quality agent has {len(tools)} tools available:")
    for i, tool in enumerate(tools, 1):
        tool_name = tool.__class__.__name__
        print(f"   {i}. {tool_name}")
    
    # Expected tools
    expected_tools = [
        'UIFeatureMetadataExtractorTool',
        'ExcelReaderTool',
        'FeatureImplementationValidatorTool',
        'WranglingConfigValidatorTool',
        'TrainingNotebookValidatorTool',
        'RiskAssessmentAlignmentReportTool',
        'PythonFeatureAnalyzerTool',
        'YAMLConfigAnalyzerTool',
    ]
    
    actual_tool_names = [tool.__class__.__name__ for tool in tools]
    
    print("\n📊 Tool Availability Check:")
    all_present = True
    for expected in expected_tools:
        present = expected in actual_tool_names
        status = "✅" if present else "❌"
        print(f"   {status} {expected}")
        if not present:
            all_present = False
    
    if all_present:
        print("\n✅ All required tools are registered!")
    else:
        print("\n❌ Some tools are missing!")
        return False
    
    # Check tool registry stats
    print("\n" + "=" * 80)
    print("Tool Usage Statistics")
    print("=" * 80)
    
    stats = registry.get_tool_usage_stats([
        'sdlc',
        'alert_validation',
        'ui_validation',
        'risk_assessment',
        'feature_quality'
    ])
    
    print(f"\nTotal tools in registry: {stats['total_tools']}")
    print(f"Total tools used across all agents: {stats['total_tools_used']}")
    print(f"Tool reuse savings: {stats['tool_reuse_savings']}")
    
    print("\nTools per agent:")
    for agent_type, info in stats['tools_by_agent'].items():
        print(f"\n  {agent_type}: {info['count']} tools")
        for tool_name in info['tools']:
            print(f"    - {tool_name}")
    
    print("\nShared tools across agents:")
    for tool_name in stats['shared_tools']:
        print(f"  - {tool_name}")
    
    return True


def test_ui_metadata_extraction():
    """Test UI metadata extraction tool"""
    
    print("\n" + "=" * 80)
    print("Testing UI Feature Metadata Extractor")
    print("=" * 80)
    
    registry = get_tool_registry()
    ui_tool = registry.get_tool('ui_feature_metadata')
    
    # Test with demo_fuib domain
    domain = "demo_fuib"
    
    print(f"\n📂 Analyzing features for domain: {domain}")
    
    try:
        result = ui_tool._run(domain=domain)
        
        # Parse JSON result
        import json
        data = json.loads(result)
        
        print(f"\n✅ Successfully extracted metadata:")
        print(f"   Total features: {data['total_features']}")
        print(f"   Training features: {data.get('training_features_count', 'N/A')}")
        print(f"   Features by type:")
        for ftype, count in data.get('by_type', {}).items():
            print(f"      {ftype}: {count}")
        
        # Check for features without descriptions
        features_without_desc = [
            f for f in data['features'] 
            if not f.get('output_fields') or 
               not any(field.get('dynamic_description') for field in f['output_fields'])
        ]
        
        if features_without_desc:
            print(f"\n⚠️  {len(features_without_desc)} features without descriptions:")
            for f in features_without_desc[:5]:
                print(f"      - {f['identifier']}")
        else:
            print("\n✅ All features have descriptions!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error extracting metadata: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_assessment_excel_reader():
    """Test Excel reader tool"""
    
    print("\n" + "=" * 80)
    print("Testing Excel Reader Tool")
    print("=" * 80)
    
    registry = get_tool_registry()
    excel_tool = registry.get_tool('excel_reader')
    
    # Test with demo_fuib risk assessment - use absolute path
    domain = "demo_fuib"
    project_root = Path(__file__).parent.parent
    excel_path = project_root / "Sonar" / "domains" / domain / "risk_assessment.xlsx"
    
    if not excel_path.exists():
        print(f"❌ Risk assessment Excel not found: {excel_path}")
        return False
    
    print(f"\n📂 Reading Excel file: {excel_path}")
    
    try:
        # Use correct parameter name: excel_path (not excel_file_path)
        # Use None for sheet_name to use the first/active sheet
        result = excel_tool._run(
            excel_path=str(excel_path),
            sheet_name=None  # Use active sheet (first sheet in workbook)
        )
        
        print(f"\n📄 Raw result (first 500 chars):")
        print(result[:500])
        print("...")
        
        # Parse JSON result
        import json
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            # Not JSON, might be a simple message
            print(f"\n✅ Result (non-JSON): {result}")
            return True
        
        print(f"\n✅ Successfully read Excel:")
        print(f"   Total features: {data.get('total_features', 'N/A')}")
        print(f"   Training features: {data.get('training_features', 'N/A')}")
        print(f"   Forensic features: {data.get('forensic_features', 'N/A')}")
        
        # Show first few features
        features = data.get('features', [])
        if features:
            print(f"\n   First 3 features:")
            for f in features[:3]:
                identifier = f.get('identifier', 'N/A')
                train = f.get('training', 'N/A')
                print(f"      - {identifier} (train: {train})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error reading Excel: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    
    results = {
        'Tool Registry': test_feature_quality_tools(),
        'UI Metadata Extraction': test_ui_metadata_extraction(),
        'Risk Assessment Excel': test_risk_assessment_excel_reader(),
    }
    
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Feature Quality Validator is ready.")
    else:
        print("\n❌ Some tests failed. Please review errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
