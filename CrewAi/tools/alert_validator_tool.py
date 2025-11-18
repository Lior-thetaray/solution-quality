"""
Alert Validator Tool for CrewAI
Wraps the standalone alert_validator.py as a CrewAI tool
"""

from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Import the standalone validator
sys.path.append(str(Path(__file__).parent.parent))
from alert_validator import AlertValidator


class AlertValidatorInput(BaseModel):
    """Input schema for AlertValidatorTool"""
    data_dir: str = Field(
        default="data",
        description="Directory containing CSV files (tr_alert_table.csv, activity_risk_table.csv, evaluated_activities.csv)"
    )


class AlertValidatorTool(BaseTool):
    name: str = "Alert Quality Validator"
    description: str = """
    Runs comprehensive alert quality validation including:
    - Alert count analysis (consolidation metrics)
    - Duplicate detection (suppression failures)
    - Monthly distribution
    - Data quality checks (cross-table consistency)
    - Alert metadata quality (severity, status, assignment)
    - Risk metadata quality (severity, categories, suppression config)
    - Activity score distribution
    - Temporal pattern analysis
    
    Returns a complete JSON report with metrics, validations, and recommendations.
    """
    args_schema: Type[BaseModel] = AlertValidatorInput
    
    def _run(self, data_dir: str = "data") -> str:
        """Execute alert validation and return JSON report"""
        validator = AlertValidator(data_dir=data_dir)
        report = validator.generate_report()
        
        # Return formatted report
        import json
        return json.dumps(report, indent=2)
