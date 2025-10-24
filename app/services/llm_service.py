"""
LLM Service for intelligent query interpretation and code generation
"""
from openai import OpenAI
from app.core.config import settings
import json
from typing import Dict, Any, Optional
import pandas as pd
import requests


class LLMService:
    """Service to interact with LLM for query interpretation"""
    
    def __init__(self):
        self.use_ollama = getattr(settings, 'USE_OLLAMA', False)
        
        if self.use_ollama:
            self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
            self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
            self.client = None
            print(f"🤖 Using Ollama: {self.model} at {self.ollama_url}")
        else:
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "not-set":
                raise ValueError("OPENAI_API_KEY is required when USE_OLLAMA=False")
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_MODEL
            print(f"🤖 Using OpenAI: {self.model}")
    
    def generate_pandas_code(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str = "df"
    ) -> Dict[str, Any]:
        """
        Generate pandas code to answer a natural language query
        
        Args:
            query: Natural language query from user
            df_info: Information about the DataFrame (columns, dtypes, sample)
            sheet_name: Variable name to use for the DataFrame in code
            
        Returns:
            Dict with generated code, explanation, and metadata
        """
        
        system_prompt = self._create_system_prompt()
        user_prompt = self._create_user_prompt(query, df_info, sheet_name)
        
        try:
            if self.use_ollama:
                # Use Ollama (local, free)
                response = self._call_ollama(system_prompt, user_prompt)
            else:
                # Use OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                response = response.choices[0].message.content
            
            result = json.loads(response)
            
            # Validate the response structure
            if "code" not in result:
                raise ValueError("LLM response missing 'code' field")
            
            return {
                "success": True,
                "code": result.get("code", ""),
                "explanation": result.get("explanation", ""),
                "operation_type": result.get("operation_type", "unknown"),
                "creates_new_column": result.get("creates_new_column", False),
                "new_column_name": result.get("new_column_name", None),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "code": None,
                "explanation": None,
                "operation_type": None,
                "creates_new_column": False,
                "new_column_name": None,
                "error": f"LLM error: {str(e)}"
            }
    
    def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama API (local LLM)"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()['message']['content']
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM"""
        return """You are an expert data analyst and Python programmer specializing in pandas operations.

Your task is to generate SAFE, EXECUTABLE pandas code to answer user queries about Excel data.

CRITICAL RULES:
1. The DataFrame variable is named 'df' (already loaded)
2. Generate ONLY pandas/numpy code - no file I/O, no imports
3. Store the final result in a variable called 'result'
4. The result should be a DataFrame, Series, or simple value (int, float, str, dict, list)
5. Use vectorized operations - avoid loops when possible
6. Handle missing data appropriately (dropna, fillna)
7. For aggregations, return a DataFrame or dict format
8. For filtering, return the filtered DataFrame
9. For new columns, modify df and set result = df
10. NEVER use eval(), exec(), or dynamic code execution
11. Keep code clean, efficient, and well-commented

RESPONSE FORMAT (JSON):
{
    "code": "# Your pandas code here\\nresult = df.groupby('column').mean()",
    "explanation": "Brief explanation of what the code does",
    "operation_type": "aggregation|filter|math|date|pivot|join|other",
    "creates_new_column": true/false,
    "new_column_name": "column_name or null"
}

EXAMPLES:

Query: "Calculate average salary by department"
Response:
{
    "code": "# Group by department and calculate mean salary\\nresult = df.groupby('department')['salary'].mean().reset_index()",
    "explanation": "Groups data by department and calculates the average salary for each department",
    "operation_type": "aggregation",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Add a column for total compensation (salary + bonus)"
Response:
{
    "code": "# Calculate total compensation\\ndf['total_compensation'] = df['salary'] + df['bonus']\\nresult = df",
    "explanation": "Creates a new column 'total_compensation' by adding salary and bonus",
    "operation_type": "math",
    "creates_new_column": true,
    "new_column_name": "total_compensation"
}

Query: "Show employees earning more than 50000"
Response:
{
    "code": "# Filter employees with salary > 50000\\nresult = df[df['salary'] > 50000]",
    "explanation": "Filters the dataset to show only employees with salary greater than 50000",
    "operation_type": "filter",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Extract year from join_date"
Response:
{
    "code": "# Extract year from join_date\\ndf['join_year'] = pd.to_datetime(df['join_date']).dt.year\\nresult = df",
    "explanation": "Extracts the year from join_date column and creates a new column join_year",
    "operation_type": "date",
    "creates_new_column": true,
    "new_column_name": "join_year"
}

Query: "Create pivot table with department and average salary"
Response:
{
    "code": "# Create pivot table\\nresult = df.pivot_table(values='salary', index='department', aggfunc='mean').reset_index()",
    "explanation": "Creates a pivot table showing average salary for each department",
    "operation_type": "pivot",
    "creates_new_column": false,
    "new_column_name": null
}

Always ensure your code is safe, efficient, and directly answers the user's query."""
    
    def _create_user_prompt(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str
    ) -> str:
        """Create the user prompt with query and data context"""
        
        columns_info = "\n".join([
            f"  - {col} ({dtype})" 
            for col, dtype in zip(df_info['columns'], df_info['dtypes'])
        ])
        
        sample_data = df_info.get('sample_data', 'Not available')
        
        return f"""USER QUERY: {query}

DATAFRAME INFORMATION:
Variable name: {sheet_name}
Shape: {df_info['shape'][0]} rows × {df_info['shape'][1]} columns

COLUMNS AND TYPES:
{columns_info}

SAMPLE DATA (first 3 rows):
{sample_data}

STATISTICS:
{df_info.get('statistics', 'Not available')}

Generate pandas code to answer this query. Return valid JSON only."""
    
    def validate_and_enhance_code(self, code: str) -> str:
        """
        Validate and enhance the generated code for safety
        
        Args:
            code: Generated pandas code
            
        Returns:
            Enhanced and validated code
        """
        # Remove any potentially dangerous operations
        forbidden_keywords = [
            'eval', 'exec', 'compile', '__import__', 
            'open', 'file', 'input', 'os.', 'sys.',
            'subprocess', 'socket', 'requests'
        ]
        
        for keyword in forbidden_keywords:
            if keyword in code.lower():
                raise ValueError(f"Forbidden operation detected: {keyword}")
        
        # Ensure imports are limited
        allowed_imports = ['import pandas as pd', 'import numpy as np', 'from datetime import']
        
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                if not any(allowed in line for allowed in allowed_imports):
                    raise ValueError(f"Unauthorized import: {line}")
        
        return code