"""Custom tools for analyzing ThetaRay solution codebases."""

from crewai.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os
import ast
import yaml
import json
from pathlib import Path


class FileAnalysisInput(BaseModel):
    """Input schema for file analysis tools."""
    domain: str = Field(..., description="Domain name to analyze (e.g., 'demo_fuib', 'default')")
    file_pattern: Optional[str] = Field(None, description="Optional glob pattern for specific files")


class PythonFeatureAnalyzerTool(BaseTool):
    name: str = "Python Feature Analyzer"
    description: str = (
        "Analyzes Python feature files in Sonar/domains/{domain}/features/ to extract "
        "feature metadata including identifiers, trace_query methods, output_fields, "
        "and inheritance from AggFeature. Also tracks cross-domain imports and validates "
        "import availability. Returns structured JSON."
    )
    args_schema: Type[BaseModel] = FileAnalysisInput
    
    def _extract_imports(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Extract import statements from AST."""
        imports = {
            "common": [],
            "other_domains": [],
            "thetaray": [],
            "external": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                items = [alias.name for alias in node.names]
                
                if module.startswith("common."):
                    imports["common"].append({"module": module, "items": items})
                elif module.startswith("demo_") or module.startswith("default.") or module.startswith("party_"):
                    imports["other_domains"].append({"module": module, "items": items})
                elif module.startswith("thetaray."):
                    imports["thetaray"].append({"module": module, "items": items})
                else:
                    imports["external"].append({"module": module, "items": items})
        
        return imports
    
    def _validate_import(self, import_module: str) -> bool:
        """Check if an imported module file exists."""
        # Convert module path to file path
        # e.g., "common.libs.config.loader" -> "../Sonar/domains/common/libs/config/loader.py"
        parts = import_module.split(".")
        if parts[0] in ["common", "default"] or parts[0].startswith("demo_") or parts[0].startswith("party_"):
            file_path = Path(f"../Sonar/domains/{'/'.join(parts)}.py")
            return file_path.exists()
        return True  # Assume external/thetaray imports are valid
    
    def _run(self, domain: str, file_pattern: Optional[str] = None) -> str:
        """Execute the feature analysis."""
        features_path = Path(f"../Sonar/domains/{domain}/features")
        
        if not features_path.exists():
            return json.dumps({"error": f"Features path not found: {features_path}"})
        
        features = []
        all_imports = {
            "common": [],
            "other_domains": [],
            "thetaray": [],
            "external": []
        }
        missing_imports = []
        
        # Recursively find all .py files
        for py_file in features_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
                
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                # Extract imports from this file
                file_imports = self._extract_imports(tree)
                
                # Merge imports
                for key in all_imports:
                    for imp in file_imports[key]:
                        if imp not in all_imports[key]:
                            all_imports[key].append(imp)
                            
                        # Validate common and other_domains imports
                        if key in ["common", "other_domains"]:
                            if not self._validate_import(imp["module"]):
                                missing_imports.append({
                                    "file": str(py_file.relative_to(features_path.parent)),
                                    "import": imp["module"]
                                })
                    
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check if inherits from AggFeature or BaseFeature
                        inherits_agg = any(
                            base.id == 'AggFeature' if isinstance(base, ast.Name) else False
                            for base in node.bases
                        )
                        
                        if inherits_agg or 'Feature' in node.name:
                            feature_info = {
                                "file": str(py_file.relative_to(features_path.parent)),
                                "class_name": node.name,
                                "has_trace_query": False,
                                "has_output_fields": False,
                                "has_identifier": False,
                                "methods": []
                            }
                            
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    feature_info["methods"].append(item.name)
                                    if item.name == "trace_query":
                                        feature_info["has_trace_query"] = True
                                elif isinstance(item, ast.FunctionDef) and hasattr(item, 'decorator_list'):
                                    if any(d.id == 'property' if isinstance(d, ast.Name) else False 
                                          for d in item.decorator_list):
                                        if item.name == "output_fields":
                                            feature_info["has_output_fields"] = True
                                        elif item.name == "identifier":
                                            feature_info["has_identifier"] = True
                            
                            features.append(feature_info)
            
            except Exception as e:
                continue
        
        result = {
            "domain": domain,
            "features": features,
            "total": len(features),
            "imports": {
                "common_modules": len(all_imports["common"]),
                "other_domains": len(all_imports["other_domains"]),
                "thetaray_apis": len(all_imports["thetaray"]),
                "details": all_imports
            },
            "missing_imports": missing_imports
        }
        
        return json.dumps(result, indent=2)


class YAMLConfigAnalyzerTool(BaseTool):
    name: str = "YAML Config Analyzer"
    description: str = (
        "Parses YAML configuration files in Sonar/domains/{domain}/config/ to extract "
        "active features, training flags, and global parameters. Returns structured JSON."
    )
    args_schema: Type[BaseModel] = FileAnalysisInput
    
    def _run(self, domain: str, file_pattern: Optional[str] = None) -> str:
        """Execute the YAML config analysis."""
        config_path = Path(f"../Sonar/domains/{domain}/config/core")
        
        if not config_path.exists():
            return json.dumps({"error": f"Config path not found: {config_path}"})
        
        configs = {
            "global": {},
            "wrangling_configs": [],
            "active_features": []
        }
        
        # Parse global.yaml
        global_yaml = config_path / "global.yaml"
        if global_yaml.exists():
            try:
                with open(global_yaml, 'r') as f:
                    configs["global"] = yaml.safe_load(f)
            except Exception as e:
                configs["global_error"] = str(e)
        
        # Find and parse wrangling.yaml files
        for wrangling_file in config_path.rglob("wrangling.yaml"):
            try:
                with open(wrangling_file, 'r') as f:
                    wrangling_data = yaml.safe_load(f)
                    
                    config_entry = {
                        "file": str(wrangling_file.relative_to(config_path)),
                        "features": []
                    }
                    
                    if wrangling_data and "requested_features" in wrangling_data:
                        for feature_id, versions in wrangling_data["requested_features"].items():
                            for version, settings in versions.items():
                                if settings.get("active", False):
                                    feature_entry = {
                                        "identifier": feature_id,
                                        "version": version,
                                        "train": settings.get("train", False),
                                        "params": settings.get("params", {})
                                    }
                                    config_entry["features"].append(feature_entry)
                                    configs["active_features"].append(feature_entry)
                    
                    configs["wrangling_configs"].append(config_entry)
            
            except Exception as e:
                continue
        
        return json.dumps(configs, indent=2)


class DatasetAnalyzerTool(BaseTool):
    name: str = "Dataset Analyzer"
    description: str = (
        "Analyzes dataset Python files in Sonar/domains/{domain}/datasets/ to extract "
        "DataSet definitions, ingestion modes, field lists, and metadata. Returns JSON."
    )
    args_schema: Type[BaseModel] = FileAnalysisInput
    
    def _run(self, domain: str, file_pattern: Optional[str] = None) -> str:
        """Execute the dataset analysis."""
        datasets_path = Path(f"../Sonar/domains/{domain}/datasets")
        
        if not datasets_path.exists():
            return json.dumps({"error": f"Datasets path not found: {datasets_path}"})
        
        datasets = []
        
        for py_file in datasets_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                
                dataset_info = {
                    "file": py_file.name,
                    "has_ingestion_mode": "IngestionMode." in content,
                    "ingestion_mode": None,
                    "has_append": "IngestionMode.APPEND" in content,
                    "has_update": "IngestionMode.UPDATE" in content,
                    "has_overwrite": "IngestionMode.OVERWRITE" in content,
                    "has_field_list": "field_list=" in content,
                    "identifier": None
                }
                
                # Extract identifier
                if "identifier='" in content or 'identifier="' in content:
                    import re
                    match = re.search(r'identifier=[\'"]([^\'"]+)[\'"]', content)
                    if match:
                        dataset_info["identifier"] = match.group(1)
                
                # Determine ingestion mode
                if dataset_info["has_append"]:
                    dataset_info["ingestion_mode"] = "APPEND"
                elif dataset_info["has_update"]:
                    dataset_info["ingestion_mode"] = "UPDATE"
                elif dataset_info["has_overwrite"]:
                    dataset_info["ingestion_mode"] = "OVERWRITE"
                
                datasets.append(dataset_info)
            
            except Exception as e:
                continue
        
        return json.dumps({"domain": domain, "datasets": datasets, "total": len(datasets)}, indent=2)


class DAGAnalyzerTool(BaseTool):
    name: str = "DAG Analyzer"
    description: str = (
        "Analyzes Airflow DAG files in Sonar/dags/{domain}/ to extract task definitions, "
        "dependencies, and pipeline flow. Returns structured JSON with task ordering."
    )
    args_schema: Type[BaseModel] = FileAnalysisInput
    
    def _run(self, domain: str, file_pattern: Optional[str] = None) -> str:
        """Execute the DAG analysis."""
        dag_paths = [
            Path(f"../Sonar/dags/{domain}"),
            Path("../Sonar/dags/default")
        ]
        
        dags_info = []
        
        for dag_path in dag_paths:
            if not dag_path.exists():
                continue
            
            for py_file in dag_path.glob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    
                    dag_info = {
                        "file": str(py_file),
                        "has_run_notebook_operator": "RunNotebookOperator" in content,
                        "tasks": [],
                        "has_task_dependencies": ">>" in content,
                        "contains_keywords": {
                            "upload": "upload" in content.lower(),
                            "wrangling": "wrangling" in content.lower(),
                            "training": "train" in content.lower(),
                            "detection": "detect" in content.lower(),
                            "decisioning": "decision" in content.lower(),
                            "distribution": "distribut" in content.lower(),
                            "drift": "drift" in content.lower()
                        }
                    }
                    
                    # Extract task_id patterns
                    import re
                    task_ids = re.findall(r'task_id=[\'"]([^\'"]+)[\'"]', content)
                    dag_info["tasks"] = task_ids
                    
                    dags_info.append(dag_info)
                
                except Exception as e:
                    continue
        
        return json.dumps({"domain": domain, "dags": dags_info, "total": len(dags_info)}, indent=2)


class NotebookAnalyzerTool(BaseTool):
    name: str = "Notebook Analyzer"
    description: str = (
        "Lists and categorizes Jupyter notebooks in Sonar/domains/{domain}/notebooks/ "
        "to identify drift monitoring, algo validation, and pipeline notebooks."
    )
    args_schema: Type[BaseModel] = FileAnalysisInput
    
    def _run(self, domain: str, file_pattern: Optional[str] = None) -> str:
        """Execute the notebook analysis."""
        notebooks_path = Path(f"../Sonar/domains/{domain}/notebooks")
        
        if not notebooks_path.exists():
            return json.dumps({"error": f"Notebooks path not found: {notebooks_path}"})
        
        notebooks = {
            "all": [],
            "drift_monitoring": [],
            "algo_validation": [],
            "wrangling": [],
            "training": [],
            "evaluation": [],
            "distribution": [],
            "other": []
        }
        
        for nb_file in notebooks_path.rglob("*.ipynb"):
            filename = nb_file.name.lower()
            notebooks["all"].append(nb_file.name)
            
            if "drift" in filename:
                notebooks["drift_monitoring"].append(nb_file.name)
            elif "algo" in filename and "valid" in filename:
                notebooks["algo_validation"].append(nb_file.name)
            elif "wrangl" in filename:
                notebooks["wrangling"].append(nb_file.name)
            elif "train" in filename:
                notebooks["training"].append(nb_file.name)
            elif "eval" in filename or "detect" in filename:
                notebooks["evaluation"].append(nb_file.name)
            elif "distribut" in filename:
                notebooks["distribution"].append(nb_file.name)
            else:
                notebooks["other"].append(nb_file.name)
        
        notebooks["total"] = len(notebooks["all"])
        notebooks["has_drift"] = len(notebooks["drift_monitoring"]) > 0
        notebooks["has_algo_validation"] = len(notebooks["algo_validation"]) > 0
        
        return json.dumps(notebooks, indent=2)