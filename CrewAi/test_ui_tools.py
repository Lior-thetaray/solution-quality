#!/usr/bin/env python3
"""
Test UI validation tools without running the agent (save tokens)
Usage: python3 test_ui_tools.py demo_fuib
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.code_analysis_tools import PythonFeatureAnalyzerTool, YAMLConfigAnalyzerTool

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "demo_fuib"
    
    print(f"\n{'='*80}")
    print(f"  UI VALIDATION TOOLS TEST - Domain: {domain}")
    print(f"{'='*80}\n")
    
    # Initialize tools
    feature_analyzer = PythonFeatureAnalyzerTool()
    yaml_analyzer = YAMLConfigAnalyzerTool()
    
    print("🔧 Tool 1: Python Feature Analyzer")
    print("-" * 80)
    
    # Test feature analyzer
    print(f"📂 Analyzing features for domain: {domain}\n")
    
    result = feature_analyzer._run(domain)
    
    # Parse result
    feature_data = json.loads(result)
    
    print(f"✅ Found {feature_data['total']} features\n")
    
    # Show sample features with their Field metadata
    print("📋 Sample Features (first 5):")
    for i, feature in enumerate(feature_data['features'][:5], 1):
        print(f"\n{i}. {feature.get('identifier', feature.get('class_name', 'UNKNOWN'))}")
        print(f"   Class: {feature.get('class_name', 'N/A')}")
        print(f"   File: {feature['file']}")
        print(f"   Has Trace Query: {feature.get('has_trace_query', False)}")
        print(f"   Has Output Fields: {feature.get('has_output_fields', False)}")
    
    print("\n" + "="*80)
    print("🔧 Tool 2: YAML Config Analyzer")
    print("-" * 80)
    
    # Test YAML analyzer
    print(f"📂 Analyzing config for domain: {domain}\n")
    
    yaml_result = yaml_analyzer._run(domain)
    yaml_data = json.loads(yaml_result)
    
    print(f"✅ Config loaded successfully\n")
    print(f"📊 Features in config: {len(yaml_data.get('features', []))}")
    
    # Show training vs forensic breakdown
    training_features = [f for f in yaml_data.get('features', []) if f.get('train') is True]
    forensic_features = [f for f in yaml_data.get('features', []) if f.get('train') is False]
    
    print(f"   - Training features: {len(training_features)}")
    print(f"   - Forensic features: {len(forensic_features)}")
    
    print("\n📋 Training Features (with train: true):")
    for f in training_features[:5]:
        print(f"   - {f.get('class_name', 'N/A')} (active: {f.get('active', False)})")
    
    print("\n" + "="*80)
    print("🎯 UI Validation Analysis")
    print("-" * 80)
    
    # Cross-reference: Check which features have trace queries
    features_with_trace = [f for f in feature_data['features'] if f.get('has_trace_query')]
    features_without_trace = [f for f in feature_data['features'] if not f.get('has_trace_query')]
    
    print(f"\n✅ Features with trace_query: {len(features_with_trace)}/{feature_data['total']}")
    print(f"❌ Features without trace_query: {len(features_without_trace)}/{feature_data['total']}")
    
    if features_without_trace:
        print("\n   Features missing trace_query:")
        for f in features_without_trace[:5]:
            print(f"      - {f.get('identifier', f.get('class_name', 'UNKNOWN'))}")
    
    # Find Z-score features
    zscore_features = [f for f in feature_data['features'] if 'z_score' in f.get('identifier', f.get('class_name', '')).lower()]
    print(f"\n📊 Z-score features: {len(zscore_features)}")
    for zf in zscore_features:
        identifier = zf.get('identifier', zf.get('class_name', 'UNKNOWN'))
        print(f"   - {identifier} (trace_query: {zf.get('has_trace_query', False)})")
    
    # Find count features
    count_features = [f for f in feature_data['features'] if f.get('identifier', f.get('class_name', '')).startswith('cnt_')]
    print(f"\n🔢 Count features: {len(count_features)}")
    for cf in count_features[:3]:
        identifier = cf.get('identifier', cf.get('class_name', 'UNKNOWN'))
        print(f"   - {identifier} (trace_query: {cf.get('has_trace_query', False)})")
    
    # Find sum features
    sum_features = [f for f in feature_data['features'] if f.get('identifier', f.get('class_name', '')).startswith('sum_')]
    print(f"\n💰 Sum features: {len(sum_features)}")
    for sf in sum_features[:3]:
        identifier = sf.get('identifier', sf.get('class_name', 'UNKNOWN'))
        print(f"   - {identifier} (trace_query: {sf.get('has_trace_query', False)})")
    
    print("\n" + "="*80)
    print("✅ Tool testing complete!")
    print("="*80 + "\n")
    
    # Save detailed output
    output_dir = Path("reports") / "ui_tool_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / f"features_{domain}.json", 'w') as f:
        json.dump(feature_data, f, indent=2)
    
    with open(output_dir / f"config_{domain}.json", 'w') as f:
        json.dump(yaml_data, f, indent=2)
    
    print(f"📁 Detailed output saved to: {output_dir}/")

if __name__ == "__main__":
    main()
