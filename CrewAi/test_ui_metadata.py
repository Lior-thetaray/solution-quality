#!/usr/bin/env python3
"""
Test the new UI Feature Metadata Extractor tool
Usage: python3 test_ui_metadata.py demo_fuib
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.ui_validation_tools import UIFeatureMetadataExtractorTool

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "demo_fuib"
    
    print(f"\n{'='*80}")
    print(f"  UI FEATURE METADATA EXTRACTION TEST")
    print(f"  Domain: {domain}")
    print(f"{'='*80}\n")
    
    tool = UIFeatureMetadataExtractorTool()
    
    print("🔧 Extracting UI metadata by instantiating features...")
    print("   (This actually runs the Python code)\n")
    
    result = tool._run(domain)
    data = json.loads(result)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return
    
    print(f"✅ Successfully extracted metadata from {data['total_features']} features\n")
    
    print(f"📊 Summary:")
    print(f"   - Training features: {data['training_features_count']}")
    print(f"   - Features with UI descriptions: {data['features_with_descriptions']}")
    print(f"   - Extraction errors: {len(data.get('extraction_errors', []))}")
    
    print(f"\n📈 Features by type:")
    for ftype, count in data['by_type'].items():
        print(f"   - {ftype}: {count}")
    
    # Show sample features with descriptions
    features_with_desc = [f for f in data['features'] if f['output_fields']]
    
    print(f"\n{'='*80}")
    print(f"📝 Features with UI Descriptions (first 3):")
    print(f"{'='*80}\n")
    
    for i, feature in enumerate(features_with_desc[:3], 1):
        print(f"{i}. {feature['identifier'] or feature['class_name']}")
        print(f"   File: {feature['file']}")
        print(f"   Type: {feature['type']}")
        print(f"   Training: {feature['is_training_feature']}")
        print(f"   Trace Query: {feature['has_trace_query']}")
        print(f"   Output Fields: {len(feature['output_fields'])}")
        
        for field in feature['output_fields']:
            print(f"\n   Field: {field.get('name', 'N/A')}")
            if 'display_name' in field:
                print(f"      Display Name: {field['display_name']}")
            if 'category' in field:
                print(f"      Category: {field['category']}")
            if 'dynamic_description' in field:
                desc = field['dynamic_description']
                print(f"      Dynamic Description: {desc[:150]}...")
            elif 'description' in field:
                desc = field['description']
                print(f"      Description: {desc[:150]}...")
        print()
    
    # Show features WITHOUT descriptions (problems!)
    features_no_desc = [f for f in data['features'] if not f['output_fields'] and f['is_training_feature']]
    
    if features_no_desc:
        print(f"{'='*80}")
        print(f"⚠️  Training Features WITHOUT UI Descriptions:")
        print(f"{'='*80}\n")
        for feature in features_no_desc[:10]:
            print(f"   - {feature['identifier'] or feature['class_name']} ({feature['type']})")
    
    # Show extraction errors
    if data.get('extraction_errors'):
        print(f"\n{'='*80}")
        print(f"❌ Extraction Errors ({len(data['extraction_errors'])}):")
        print(f"{'='*80}\n")
        for err in data['extraction_errors'][:5]:
            print(f"   File: {err.get('file', 'N/A')}")
            print(f"   Error: {err.get('error', 'N/A')}\n")
    
    # Save full output
    output_dir = Path("reports") / "ui_metadata_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{domain}_ui_metadata.json"
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"{'='*80}")
    print(f"✅ Full output saved to: {output_file}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
