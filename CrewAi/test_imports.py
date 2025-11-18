#!/usr/bin/env python3
"""Test import tracking in feature analyzer."""

from tools.code_analysis_tools import PythonFeatureAnalyzerTool
import json

tool = PythonFeatureAnalyzerTool()
result = tool._run(domain='demo_fuib')
data = json.loads(result)

print('Domain:', data['domain'])
print('Total features:', data['total'])
print('\nImport Summary:')
print(f"  Common modules: {data['imports']['common_modules']}")
print(f"  Other domains: {data['imports']['other_domains']}")
print(f"  ThetaRay APIs: {data['imports']['thetaray_apis']}")

if data['imports']['details']['common']:
    print('\nCommon imports:')
    for imp in data['imports']['details']['common'][:5]:
        print(f"  - {imp['module']}: {', '.join(imp['items'][:3])}")

if data['imports']['details']['other_domains']:
    print('\nOther domain imports:')
    for imp in data['imports']['details']['other_domains'][:5]:
        print(f"  - {imp['module']}: {', '.join(imp['items'][:3])}")

if data['missing_imports']:
    print(f'\n⚠️  Missing imports found: {len(data["missing_imports"])}')
    for miss in data['missing_imports'][:5]:
        print(f"  - {miss['file']}: {miss['import']}")
else:
    print('\n✅ All imports validated successfully')
