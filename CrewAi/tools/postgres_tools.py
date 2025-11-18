"""PostgreSQL read-only query tool for validation agents."""

from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
import json
from sqlalchemy import create_engine
from contextlib import closing
import pandas as pd
import re


class PostgresQueryInput(BaseModel):
    """Input schema for PostgreSQL read query tool."""
    query: str = Field(..., description="SQL SELECT query to execute (read-only)")


class PostgresReadOnlyTool(BaseTool):
    name: str = "PostgreSQL Read-Only Query Tool"
    description: str = (
        "Executes READ-ONLY SELECT queries against PostgreSQL database to retrieve datasets. "
        "Returns query results as JSON. Only SELECT statements are allowed - all write operations "
        "(INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE) will be rejected for safety."
    )
    args_schema: Type[BaseModel] = PostgresQueryInput
    
    # Forbidden SQL keywords that modify data
    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    def _get_engine(self):
        """Create SQLAlchemy engine for PostgreSQL connection."""
        username = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DB")
        shared_namespace = os.getenv("SHARED_NAMESPACE", "default")
        
        # Build connection string
        connection_string = (
            f"postgresql+psycopg2://{username}:{password}@"
            f"postgres.{shared_namespace}.svc.cluster.local:5432/{database}"
        )
        
        return create_engine(connection_string)
    
    def _is_read_only_query(self, query: str) -> tuple[bool, str]:
        """
        Validate that query is read-only (SELECT only).
        Returns: (is_valid, error_message)
        """
        query_upper = query.upper().strip()
        
        # Remove comments
        query_cleaned = re.sub(r'--.*$', '', query_upper, flags=re.MULTILINE)
        query_cleaned = re.sub(r'/\*.*?\*/', '', query_cleaned, flags=re.DOTALL)
        
        # Check for forbidden keywords
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', query_cleaned):
                return False, f"Write operation '{keyword}' is not allowed. Only SELECT queries are permitted."
        
        # Must start with SELECT (after whitespace)
        if not re.match(r'^\s*SELECT\b', query_cleaned):
            return False, "Query must be a SELECT statement. Only read operations are allowed."
        
        # Check for semicolon-separated multiple statements
        statements = [s.strip() for s in query_cleaned.split(';') if s.strip()]
        if len(statements) > 1:
            return False, "Multiple statements are not allowed. Execute one SELECT query at a time."
        
        return True, ""
    
    def _run(self, query: str) -> str:
        """Execute read-only SQL query and return results."""
        # Validate query is read-only
        is_valid, error_msg = self._is_read_only_query(query)
        if not is_valid:
            return json.dumps({
                "status": "error",
                "error": error_msg,
                "query": query
            })
        
        try:
            # Create SQLAlchemy engine
            engine = self._get_engine()
            
            # Execute query using pandas and return as JSON
            with closing(engine.raw_connection()) as conn:
                df = pd.read_sql(query, conn)
            
            # Convert DataFrame to JSON-serializable format
            result = {
                "status": "success",
                "rows_returned": len(df),
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient='records')
            }
            
            # Dispose engine
            engine.dispose()
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "query": query
            })
