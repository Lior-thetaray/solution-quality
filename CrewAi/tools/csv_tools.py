"""CSV dataset reader tool for validation agents."""

from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
import json
import pandas as pd
from pathlib import Path


class CSVReaderInput(BaseModel):
    """Input schema for CSV reader tool."""
    filename: str = Field(..., description="Name of the CSV file to read (e.g., 'customers.csv', 'transactions.csv')")
    limit: Optional[int] = Field(None, description="Maximum number of rows to return (default: all rows)")


class CSVDatasetReaderTool(BaseTool):
    name: str = "CSV Dataset Reader"
    description: str = (
        "Reads CSV files containing datasets and returns data as JSON. "
        "Use this to load and analyze dataset files for validation. "
        "CSV files should be placed in the 'data/' directory."
    )
    args_schema: Type[BaseModel] = CSVReaderInput
    
    def _get_csv_path(self, filename: str) -> Path:
        """Get full path to CSV file in data directory."""
        # Look in data/ directory
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / filename
    
    def _run(self, filename: str, limit: Optional[int] = None) -> str:
        """Read CSV file and return as JSON."""
        try:
            csv_path = self._get_csv_path(filename)
            
            if not csv_path.exists():
                return json.dumps({
                    "status": "error",
                    "error": f"CSV file not found: {filename}",
                    "expected_path": str(csv_path),
                    "tip": "Place CSV files in the 'data/' directory"
                })
            
            # Read CSV file
            df = pd.read_csv(csv_path)
            
            # Apply limit if specified
            if limit and limit > 0:
                df = df.head(limit)
            
            # Get basic statistics
            stats = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
            }
            
            result = {
                "status": "success",
                "filename": filename,
                "rows_returned": len(df),
                "statistics": stats,
                "data": df.to_dict(orient='records')
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "filename": filename
            })


class CSVListInput(BaseModel):
    """Input schema for CSV list tool (no arguments needed)."""
    pass


class CSVListTool(BaseTool):
    name: str = "CSV File Lister"
    description: str = (
        "Lists all available CSV files in the data directory. "
        "Use this to see what datasets are available for analysis."
    )
    args_schema: Type[BaseModel] = CSVListInput
    
    def _run(self) -> str:
        """List all CSV files in data directory."""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            
            csv_files = list(data_dir.glob("*.csv"))
            
            files_info = []
            for csv_file in csv_files:
                size = csv_file.stat().st_size
                files_info.append({
                    "filename": csv_file.name,
                    "size": f"{size / 1024:.2f} KB",
                    "path": str(csv_file)
                })
            
            result = {
                "status": "success",
                "total_files": len(files_info),
                "files": files_info,
                "data_directory": str(data_dir)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e)
            })
