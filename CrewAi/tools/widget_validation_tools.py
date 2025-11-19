"""
Widget Validation Tools for ThetaRay Solution Quality
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class DomainInput(BaseModel):
    """Input schema for domain-based tools"""
    domain: str = Field(..., description="Domain name to analyze (e.g., 'demo_fuib')")


class FeatureCheckInput(BaseModel):
    """Input schema for feature-specific checks"""
    domain: str = Field(..., description="Domain name (e.g., 'demo_fuib')")
    feature_identifier: str = Field(..., description="Feature identifier to check")


def analyze_single_feature(feature_file: Path) -> Dict[str, Any]:
    """Analyze a single feature file to extract widget information"""
    try:
        content = feature_file.read_text()
    except Exception as e:
        return {
            "identifier": feature_file.stem,
            "error": str(e),
            "has_explainability": False
        }
    
    analysis = {
        "identifier": extract_identifier(content),
        "file_path": str(feature_file),
        "has_explainability": False,
        "widget_type": None,
        "has_population": False,
        "data_type": extract_data_type(content),
        "category": extract_category(content),
        "time_range_specified": False
    }
    
    # Check for ExplainabilityType
    widget_types = {
        "BEHAVIORAL": re.search(r'type\s*=\s*ExplainabilityType\.BEHAVIORAL', content),
        "CATEGORICAL": re.search(r'type\s*=\s*ExplainabilityType\.CATEGORICAL', content),
        "HISTORICAL": re.search(r'type\s*=\s*ExplainabilityType\.HISTORICAL', content),
        "BINARY": re.search(r'type\s*=\s*ExplainabilityType\.BINARY', content)
    }
    
    for widget_type, match in widget_types.items():
        if match:
            analysis["has_explainability"] = True
            analysis["widget_type"] = widget_type
            break
    
    # Check for population behavior (for HISTORICAL widgets)
    if analysis["widget_type"] == "HISTORICAL":
        population_patterns = [
            r'type\s*=\s*ExplainabilityValueType\.POPULATION',
            r'pop_avg',
            r'pop_dstnct',
            r'population'
        ]
        analysis["has_population"] = any(re.search(pattern, content, re.IGNORECASE) 
                                         for pattern in population_patterns)
        
        # Check if time range is specified
        analysis["time_range_specified"] = bool(
            re.search(r'time_range_value\s*=\s*\d+', content)
        )
    
    return analysis


def extract_identifier(content: str) -> str:
    """Extract feature identifier from content"""
    match = re.search(r'def identifier\(self\)\s*->\s*str:\s*return\s*[\'"]([^\'"]+)[\'"]', content)
    if match:
        return match.group(1)
    
    match = re.search(r'Field\s*\(\s*identifier\s*=\s*[\'"]([^\'"]+)[\'"]', content)
    if match:
        return match.group(1)
    
    return "unknown"


def extract_data_type(content: str) -> str:
    """Extract data type from Field definition"""
    match = re.search(r'data_type\s*=\s*DataType\.(\w+)', content)
    return match.group(1) if match else "unknown"


def extract_category(content: str) -> str:
    """Extract category from Field definition"""
    match = re.search(r'category\s*=\s*[\'"]([^\'"]+)[\'"]', content)
    return match.group(1) if match else "unknown"


def get_feature_characteristics(feature_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract feature characteristics for LLM-based validation (no hardcoded rules)"""
    identifier = feature_analysis["identifier"]
    
    # Detect feature patterns (informational only, LLM decides validation)
    characteristics = {
        "is_z_score": identifier.startswith("z_score"),
        "is_boolean": feature_analysis["data_type"] == "BOOLEAN",
        "appears_categorical": any(ind in identifier for ind in 
            ["cnt_distinct", "one_to_many", "many_to_one", "cp_concentration"]),
        "appears_geographic": any(geo in identifier for geo in 
            ["cntry", "country", "geo", "region", "jurisdiction"]),
        "appears_temporal": any(temp in identifier for temp in 
            ["daily", "weekly", "monthly", "period", "time"])
    }
    
    return characteristics


class AnalyzeFeatureWidgetsTool(BaseTool):
    name: str = "Analyze Feature Widgets"
    description: str = (
        "Analyzes all features in the specified domain to validate widget configurations. "
        "Returns comprehensive report on widget assignments and recommendations."
    )
    args_schema: Type[BaseModel] = DomainInput
    
    def _run(self, domain: str) -> str:
        base_path = Path(f"../Sonar/domains/{domain}/features/core")
        
        if not base_path.exists():
            return json.dumps({
                "error": f"Domain path not found: {base_path}",
                "features_analyzed": 0
            })
        
        results = {
            "domain": domain,
            "features_analyzed": 0,
            "features_with_widgets": 0,
            "features_without_widgets": 0,
            "widget_recommendations": [],
            "validation_errors": [],
            "summary": {}
        }
        
        feature_files = list(base_path.rglob("*.py"))
        
        for feature_file in feature_files:
            if feature_file.name.startswith("__"):
                continue
                
            feature_analysis = analyze_single_feature(feature_file)
            results["features_analyzed"] += 1
            
            if feature_analysis["has_explainability"]:
                results["features_with_widgets"] += 1
                characteristics = get_feature_characteristics(feature_analysis)
                
                # Provide raw data for LLM to validate against instructions
                results["widget_recommendations"].append({
                    "feature": feature_analysis["identifier"],
                    "file": str(feature_file.relative_to(Path("../Sonar/domains"))),
                    "current_widget": feature_analysis["widget_type"],
                    "data_type": feature_analysis["data_type"],
                    "category": feature_analysis["category"],
                    "has_population": feature_analysis["has_population"],
                    "time_range_specified": feature_analysis["time_range_specified"],
                    "characteristics": characteristics
                })
            else:
                results["features_without_widgets"] += 1
                results["validation_errors"].append({
                    "feature": feature_analysis["identifier"],
                    "file": str(feature_file.relative_to(Path("../Sonar/domains"))),
                    "issue": "No explainability widget defined",
                    "severity": "warning"
                })
        
        # Generate summary (counts only, no validation)
        results["summary"] = {
            "total_features": results["features_analyzed"],
            "with_widgets": results["features_with_widgets"],
            "without_widgets": results["features_without_widgets"],
            "widget_type_counts": {},
            "features_with_population": sum(
                1 for r in results["widget_recommendations"] 
                if r.get("has_population", False)
            )
        }
        
        # Count widget types
        for rec in results["widget_recommendations"]:
            widget_type = rec["current_widget"]
            results["summary"]["widget_type_counts"][widget_type] = \
                results["summary"]["widget_type_counts"].get(widget_type, 0) + 1
        
        return json.dumps(results, indent=2)


class GetWidgetBestPracticesTool(BaseTool):
    name: str = "Get Widget Best Practices"
    description: str = "Returns best practices and guidelines for widget selection"
    args_schema: Type[BaseModel] = BaseModel
    
    def _run(self) -> str:
        best_practices = {
            "widget_types": {
                "BEHAVIORAL": {
                    "description": "Stacked bar chart over time",
                    "use_cases": ["Time-series patterns", "Geographic distributions over time"],
                    "required_fields": ["time_range_value", "category_lbl", "category_var", "json_column_reference"]
                },
                "CATEGORICAL": {
                    "description": "Pie chart for category distribution",
                    "use_cases": ["One-to-many relationships", "Counterparty concentration"],
                    "required_fields": ["category_lbl", "category_var", "json_column_reference"]
                },
                "HISTORICAL": {
                    "description": "Line graph with historical trend comparison",
                    "use_cases": ["Z-score features", "Deviation from historical baseline"],
                    "required_fields": ["time_range_value", "ExplainabilityValueType.POPULATION (MANDATORY)"],
                    "validation_rules": ["MUST include population behavior", "MUST specify time range"]
                },
                "BINARY": {
                    "description": "Text-only display for boolean values",
                    "use_cases": ["True/False flags", "Binary states"],
                    "required_fields": ["Key-value pairs"]
                }
            },
            "selection_guidelines": {
                "boolean_fields": "Always use BINARY widget",
                "z_score_features": "Always use HISTORICAL with population behavior",
                "count_distinct_features": "Prefer CATEGORICAL",
                "aggregate_features": "Use BEHAVIORAL or HISTORICAL with population"
            }
        }
        
        return json.dumps(best_practices, indent=2)


class CheckFeatureWidgetRequirementsTool(BaseTool):
    name: str = "Check Feature Widget Requirements"
    description: str = "Checks if a specific feature's widget configuration meets all requirements"
    args_schema: Type[BaseModel] = FeatureCheckInput
    
    def _run(self, domain: str, feature_identifier: str) -> str:
        base_path = Path(f"../Sonar/domains/{domain}/features/core")
        
        feature_files = list(base_path.rglob("*.py"))
        target_file = None
        
        for f in feature_files:
            content = f.read_text()
            if f'return \'{feature_identifier}\'' in content or f'identifier=\'{feature_identifier}\'' in content:
                target_file = f
                break
        
        if not target_file:
            return json.dumps({
                "error": f"Feature '{feature_identifier}' not found in domain '{domain}'"
            })
        
        feature_analysis = analyze_single_feature(target_file)
        characteristics = get_feature_characteristics(feature_analysis)
        content = target_file.read_text()
        
        # Provide raw feature data for LLM to validate
        feature_details = {
            "feature": feature_identifier,
            "file": str(target_file.relative_to(Path("../Sonar/domains"))),
            "widget_type": feature_analysis["widget_type"],
            "data_type": feature_analysis["data_type"],
            "category": feature_analysis["category"],
            "has_population": feature_analysis["has_population"],
            "time_range_specified": feature_analysis["time_range_specified"],
            "characteristics": characteristics,
            "widget_fields": {}
        }
        
        # Extract widget field details for context
        widget_type = feature_analysis["widget_type"]
        
        if widget_type == "HISTORICAL":
            feature_details["widget_fields"]["has_time_range"] = bool(
                re.search(r'time_range_value\s*=\s*\d+', content)
            )
            feature_details["widget_fields"]["has_population_type"] = bool(
                re.search(r'ExplainabilityValueType\.POPULATION', content)
            )
        
        if widget_type == "BEHAVIORAL":
            feature_details["widget_fields"]["has_category_lbl"] = bool(
                re.search(r'category_lbl\s*=', content)
            )
            feature_details["widget_fields"]["has_time_range"] = bool(
                re.search(r'time_range_value\s*=\s*\d+', content)
            )
        
        return json.dumps(feature_details, indent=2)
