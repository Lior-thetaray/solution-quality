"""UI-specific tools for validating feature descriptions and display names."""

from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import sys
import json
import importlib
from pathlib import Path

# Get workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.absolute()
SONAR_PATH = WORKSPACE_ROOT / "Sonar"

# Add Sonar to Python path for imports
if str(SONAR_PATH) not in sys.path:
    sys.path.insert(0, str(SONAR_PATH))


class UIFeatureInput(BaseModel):
    """Input schema for UI feature analysis."""
    domain: str = Field(..., description="Domain name to analyze (e.g., 'demo_fuib')")


class UIFeatureMetadataExtractorTool(BaseTool):
    name: str = "UI Feature Metadata Extractor"
    description: str = (
        "Extracts UI display metadata from feature instances by actually importing and "
        "instantiating them. Returns feature identifiers, display names, descriptions, "
        "categories, and Field definitions with dynamic_description templates. "
        "This tool EXECUTES Python code to get runtime metadata."
    )
    args_schema: Type[BaseModel] = UIFeatureInput
    
    def _import_feature_class(self, domain: str, module_path: str, class_name: str) -> Optional[Any]:
        """Dynamically import a feature class."""
        try:
            # Convert file path to module path
            # e.g., "features/core/customer/one_to_many.py" -> "domains.demo_fuib.features.core.customer.one_to_many"
            rel_path = module_path.replace('features/', '').replace('.py', '').replace('/', '.')
            full_module = f"domains.{domain}.features.{rel_path}"
            
            module = importlib.import_module(full_module)
            return getattr(module, class_name, None)
        except Exception as e:
            return None
    
    def _extract_field_metadata(self, field_obj: Any) -> Dict[str, Any]:
        """Extract metadata from a Field object."""
        metadata = {}
        
        # Get all attributes
        for attr in ['name', 'display_name', 'description', 'dynamic_description', 
                     'category', 'datatype', 'business_type']:
            if hasattr(field_obj, attr):
                val = getattr(field_obj, attr)
                if val is not None:
                    metadata[attr] = str(val) if not isinstance(val, (str, int, float, bool)) else val
        
        return metadata
    
    def _run(self, domain: str) -> str:
        """Execute the UI metadata extraction."""
        # First, use Python Feature Analyzer to get feature files
        from tools.code_analysis_tools import PythonFeatureAnalyzerTool, YAMLConfigAnalyzerTool
        
        feature_analyzer = PythonFeatureAnalyzerTool()
        yaml_analyzer = YAMLConfigAnalyzerTool()
        
        # Get feature file structure
        features_result = feature_analyzer._run(domain)
        features_data = json.loads(features_result)
        
        if 'error' in features_data:
            return json.dumps({"error": features_data['error']})
        
        # Get YAML config to identify training features
        yaml_result = yaml_analyzer._run(domain)
        yaml_data = json.loads(yaml_result)
        
        # Build training feature lookup
        training_features = set()
        for config in yaml_data.get('wrangling_configs', []):
            for feat in config.get('features', []):
                if feat.get('train'):
                    training_features.add(feat['identifier'])
        
        # Now instantiate features and extract UI metadata
        ui_features = []
        errors = []
        
        for feature_info in features_data['features']:
            try:
                # Import the class
                feature_class = self._import_feature_class(
                    domain, 
                    feature_info['file'], 
                    feature_info['class_name']
                )
                
                if not feature_class:
                    errors.append({
                        "file": feature_info['file'],
                        "error": "Could not import feature class"
                    })
                    continue
                
                # Instantiate the feature
                try:
                    feature_instance = feature_class()
                except Exception as e:
                    # Some features need parameters, try with empty dict
                    try:
                        feature_instance = feature_class({})
                    except:
                        errors.append({
                            "file": feature_info['file'],
                            "class": feature_info['class_name'],
                            "error": f"Could not instantiate: {str(e)}"
                        })
                        continue
                
                # Extract metadata
                ui_metadata = {
                    "file": feature_info['file'],
                    "class_name": feature_info['class_name'],
                    "identifier": None,
                    "version": None,
                    "description": None,
                    "output_fields": [],
                    "has_trace_query": feature_info.get('has_trace_query', False),
                    "is_training_feature": False,
                    "type": "unknown"
                }
                
                # Get identifier
                if hasattr(feature_instance, 'identifier'):
                    try:
                        ui_metadata['identifier'] = feature_instance.identifier()
                    except:
                        pass
                
                # Get version
                if hasattr(feature_instance, 'version'):
                    try:
                        ui_metadata['version'] = feature_instance.version()
                    except:
                        pass
                
                # Get description
                if hasattr(feature_instance, 'description'):
                    try:
                        ui_metadata['description'] = feature_instance.description()
                    except:
                        pass
                
                # Get output fields (THIS IS KEY FOR UI VALIDATION)
                if hasattr(feature_instance, 'output_fields'):
                    try:
                        fields = feature_instance.output_fields()
                        if fields:
                            for field in fields:
                                field_meta = self._extract_field_metadata(field)
                                ui_metadata['output_fields'].append(field_meta)
                    except Exception as e:
                        errors.append({
                            "file": feature_info['file'],
                            "class": feature_info['class_name'],
                            "error": f"Could not extract output_fields: {str(e)}"
                        })
                
                # Determine feature type
                identifier = ui_metadata['identifier'] or ui_metadata['class_name']
                if identifier:
                    if identifier.lower().startswith('z_score') or 'zscore' in identifier.lower():
                        ui_metadata['type'] = 'z_score'
                    elif identifier.lower().startswith('cnt_') or identifier.lower().startswith('count_'):
                        ui_metadata['type'] = 'count'
                    elif identifier.lower().startswith('sum_') or identifier.lower().startswith('total_'):
                        ui_metadata['type'] = 'sum'
                    elif identifier.lower().startswith('max_') or identifier.lower().startswith('min_'):
                        ui_metadata['type'] = 'minmax'
                    
                    # Check if training feature
                    ui_metadata['is_training_feature'] = identifier in training_features
                
                ui_features.append(ui_metadata)
                
            except Exception as e:
                errors.append({
                    "file": feature_info['file'],
                    "error": f"Unexpected error: {str(e)}"
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
