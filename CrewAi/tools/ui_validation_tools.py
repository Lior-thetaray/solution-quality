"""UI-specific tools for validating feature descriptions and display names."""

from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import ast
import json
import re
from pathlib import Path

# Get workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.absolute()
SONAR_PATH = WORKSPACE_ROOT / "Sonar"


class UIFeatureInput(BaseModel):
    """Input schema for UI feature analysis."""
    domain: str = Field(..., description="Domain name to analyze (e.g., 'demo_fuib')")


class UIFeatureMetadataExtractorTool(BaseTool):
    name: str = "UI Feature Metadata Extractor"
    description: str = (
        "Extracts UI display metadata from feature files using AST parsing. "
        "Returns feature identifiers, Field definitions with display_name, category, "
        "description, and dynamic_description templates. Does NOT execute code."
    )
    args_schema: Type[BaseModel] = UIFeatureInput
    
    def _extract_string_value(self, node: ast.AST) -> Optional[str]:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value is not None else None
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.JoinedStr):  # f-string
            # Try to reconstruct f-string
            parts = []
            for val in node.values:
                if isinstance(val, (ast.Constant, ast.Str)):
                    parts.append(self._extract_string_value(val) or "")
                elif isinstance(val, ast.FormattedValue):
                    parts.append("{...}")
            return "".join(parts)
        return None
    
    def _extract_field_call(self, node: ast.Call) -> Optional[Dict[str, Any]]:
        """Extract Field() call parameters."""
        field_data = {}
        
        # Get positional args (name is usually first)
        if node.args:
            name_val = self._extract_string_value(node.args[0])
            if name_val:
                field_data['name'] = name_val
        
        # Get keyword arguments
        for keyword in node.keywords:
            key = keyword.arg
            if key in ['display_name', 'description', 'dynamic_description', 'category', 
                      'datatype', 'business_type']:
                val = self._extract_string_value(keyword.value)
                if val:
                    field_data[key] = val
        
        return field_data if field_data else None
    
    def _extract_method_return_value(self, method_node: ast.FunctionDef, method_name: str) -> Optional[Any]:
        """Extract return value from a simple method."""
        for node in ast.walk(method_node):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, (ast.Constant, ast.Str)):
                    return self._extract_string_value(node.value)
        return None
    
    def _parse_feature_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a single feature file using AST."""
        result = {
            "file": str(file_path.relative_to(SONAR_PATH / "domains")),
            "class_name": None,
            "identifier": None,
            "version": None,
            "description": None,
            "output_fields": [],
            "has_trace_query": False,
            "type": "unknown"
        }
        
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            # Find class definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result['class_name'] = node.name
                    
                    # Look for methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_name = item.name
                            
                            # Check for trace_query method
                            if method_name == 'trace_query':
                                result['has_trace_query'] = True
                            
                            # Extract simple return values
                            elif method_name == 'identifier':
                                val = self._extract_method_return_value(item, 'identifier')
                                if val:
                                    result['identifier'] = val
                            
                            elif method_name == 'version':
                                val = self._extract_method_return_value(item, 'version')
                                if val:
                                    result['version'] = val
                            
                            elif method_name == 'description':
                                val = self._extract_method_return_value(item, 'description')
                                if val:
                                    result['description'] = val
                            
                            # Parse output_fields method
                            elif method_name == 'output_fields':
                                for stmt in ast.walk(item):
                                    # Look for Field() calls
                                    if isinstance(stmt, ast.Call):
                                        if isinstance(stmt.func, ast.Name) and stmt.func.id == 'Field':
                                            field_data = self._extract_field_call(stmt)
                                            if field_data:
                                                result['output_fields'].append(field_data)
            
            # Determine feature type from identifier
            identifier = result['identifier'] or result['class_name'] or ""
            identifier_lower = identifier.lower()
            
            if 'z_score' in identifier_lower or 'zscore' in identifier_lower:
                result['type'] = 'z_score'
            elif identifier_lower.startswith('cnt_') or identifier_lower.startswith('count_'):
                result['type'] = 'count'
            elif identifier_lower.startswith('sum_') or identifier_lower.startswith('total_'):
                result['type'] = 'sum'
            elif identifier_lower.startswith('max_') or identifier_lower.startswith('min_'):
                result['type'] = 'minmax'
            
        except Exception as e:
            result['parse_error'] = str(e)
        
        return result
    
    def _run(self, domain: str) -> str:
        """Execute the UI metadata extraction."""
        # Get YAML config to identify training features
        from tools.code_analysis_tools import YAMLConfigAnalyzerTool
        
        yaml_analyzer = YAMLConfigAnalyzerTool()
        yaml_result = yaml_analyzer._run(domain)
        yaml_data = json.loads(yaml_result)
        
        # Build training feature lookup
        training_features = set()
        for config in yaml_data.get('wrangling_configs', []):
            for feat in config.get('features', []):
                if feat.get('train'):
                    training_features.add(feat['identifier'])
        
        # Find all feature files
        features_path = SONAR_PATH / "domains" / domain / "features"
        
        if not features_path.exists():
            return json.dumps({"error": f"Features path not found: {features_path}"})
        
        ui_features = []
        errors = []
        
        # Parse each feature file
        for py_file in features_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                feature_data = self._parse_feature_file(py_file)
                
                # Add training flag
                identifier = feature_data['identifier'] or feature_data['class_name']
                feature_data['is_training_feature'] = identifier in training_features if identifier else False
                
                if 'parse_error' in feature_data:
                    errors.append({
                        "file": feature_data['file'],
                        "error": feature_data['parse_error']
                    })
                
                ui_features.append(feature_data)
                
            except Exception as e:
                errors.append({
                    "file": str(py_file.relative_to(SONAR_PATH / "domains")),
                    "error": str(e)
                })
        
        result = {
            "domain": domain,
            "total_features": len(ui_features),
            "features": ui_features,
            "extraction_errors": errors,
            "training_features_count": len([f for f in ui_features if f['is_training_feature']]),
            "features_with_descriptions": len([f for f in ui_features if f['output_fields']]),
            "by_type": {
                "z_score": len([f for f in ui_features if f['type'] == 'z_score']),
                "count": len([f for f in ui_features if f['type'] == 'count']),
                "sum": len([f for f in ui_features if f['type'] == 'sum']),
                "minmax": len([f for f in ui_features if f['type'] == 'minmax']),
                "other": len([f for f in ui_features if f['type'] == 'unknown'])
            }
        }
        
        return json.dumps(result, indent=2)
