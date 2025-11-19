#!/usr/bin/env python3
"""
Quick test script for widget validation tools
Tests the tools directly without running the full agent workflow
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from tools.widget_validation_tools import (
    AnalyzeFeatureWidgetsTool,
    GetWidgetBestPracticesTool,
    CheckFeatureWidgetRequirementsTool
)

# Instantiate tools
analyze_tool = AnalyzeFeatureWidgetsTool()
best_practices_tool = GetWidgetBestPracticesTool()
requirements_tool = CheckFeatureWidgetRequirementsTool()


def test_widget_analysis():
    """Test the widget analysis tool"""
    print("="*80)
    print("Testing Widget Analysis Tool")
    print("="*80)
    
    domain = "demo_fuib"
    print(f"\nAnalyzing domain: {domain}")
    
    result = analyze_tool._run(domain)
    
    # Parse and display
    try:
        data = json.loads(result)
        print(f"\n✅ Successfully analyzed {data.get('features_analyzed', 0)} features")
        print(f"\nSummary:")
        summary = data.get("summary", {})
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        # Show a few recommendations
        recommendations = data.get("widget_recommendations", [])
        if recommendations:
            print(f"\nFirst 3 recommendations:")
            for rec in recommendations[:3]:
                print(f"\n  Feature: {rec['feature']}")
                print(f"  Current: {rec['current_widget']}")
                print(f"  Recommended: {rec['recommended_widget']}")
                print(f"  Optimal: {rec['is_optimal']}")
                print(f"  Has Population: {rec['has_population']}")
                print(f"  Reasoning: {rec['reasoning'][:100]}...")
        
        # Show validation errors
        errors = data.get("validation_errors", [])
        if errors:
            print(f"\n⚠️  Found {len(errors)} validation errors")
            for error in errors[:3]:
                print(f"\n  Feature: {error.get('feature', 'unknown')}")
                print(f"  Issue: {error.get('issue', 'unknown')}")
                print(f"  Severity: {error.get('severity', 'unknown')}")
        
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"Raw result: {result[:500]}")
        return False


def test_best_practices():
    """Test the best practices tool"""
    print("\n" + "="*80)
    print("Testing Best Practices Tool")
    print("="*80)
    
    result = best_practices_tool._run()
    
    try:
        data = json.loads(result)
        print("\n✅ Successfully retrieved best practices")
        print(f"\nWidget Types:")
        for widget_type, info in data.get("widget_types", {}).items():
            print(f"\n  {widget_type}:")
            print(f"    Description: {info.get('description', 'N/A')}")
            print(f"    Use Cases: {len(info.get('use_cases', []))}")
        
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        return False


def test_feature_requirements():
    """Test the feature requirements check tool"""
    print("\n" + "="*80)
    print("Testing Feature Requirements Tool")
    print("="*80)
    
    domain = "demo_fuib"
    feature = "z_score_sum_hghrsk_cntry"
    
    print(f"\nChecking feature: {feature} in domain: {domain}")
    
    result = requirements_tool._run(domain=domain, feature_identifier=feature)
    
    try:
        data = json.loads(result)
        print(f"\n✅ Successfully checked feature requirements")
        print(f"\nWidget Type: {data.get('widget_type', 'unknown')}")
        print(f"Is Optimal: {data.get('is_optimal', False)}")
        
        met = data.get('requirements_met', [])
        missing = data.get('requirements_missing', [])
        
        if met:
            print(f"\n✅ Requirements Met ({len(met)}):")
            for req in met:
                print(f"  • {req}")
        
        if missing:
            print(f"\n❌ Requirements Missing ({len(missing)}):")
            for req in missing:
                print(f"  • {req}")
        
        print(f"\nRecommendations: {data.get('recommendations', 'None')}")
        
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
        print(f"Raw result: {result[:500]}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🔍 Widget Validation Tools Test Suite")
    print("="*80)
    
    tests = [
        ("Widget Analysis", test_widget_analysis),
        ("Best Practices", test_best_practices),
        ("Feature Requirements", test_feature_requirements)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
