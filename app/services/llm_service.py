from app.core.config import settings
import json
from typing import Dict, Any, Optional, List
import pandas as pd
import requests
import re


class LLMService:
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
    
    def validate_columns_in_query(self, query: str, available_columns: List[str]) -> Dict[str, Any]:
        query_lower = query.lower()
        mentioned_columns = []
        missing_columns = []
        
        words = re.findall(r'\b\w+\b', query_lower)
        
        for word in words:
            for col in available_columns:
                col_lower = col.lower()
                col_underscore = col_lower.replace('_', ' ')
                col_no_underscore = col_lower.replace('_', '')
                
                if word in [col_lower, col_underscore, col_no_underscore]:
                    if col not in mentioned_columns:
                        mentioned_columns.append(col)
                elif col_lower in word or word in col_lower:
                    if len(word) > 3 and col not in mentioned_columns:
                        mentioned_columns.append(col)
        
        potential_columns = re.findall(r'\b[a-z_]+\b', query_lower)
        for pot_col in potential_columns:
            if pot_col not in [c.lower() for c in available_columns]:
                if pot_col not in ['by', 'and', 'or', 'the', 'from', 'to', 'in', 'on', 'with', 'for', 'of', 'as', 'is', 'show', 'create', 'calculate', 'filter', 'find', 'get', 'where', 'column', 'data', 'table', 'row', 'value', 'number', 'count', 'sum', 'average', 'mean', 'max', 'min']:
                    if len(pot_col) > 4:
                        missing_columns.append(pot_col)
        
        return {
            'valid': len(missing_columns) == 0,
            'mentioned_columns': mentioned_columns,
            'potential_missing': missing_columns
        }
    
    def generate_pandas_code(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str = "df"
    ) -> Dict[str, Any]:
        
        column_validation = self.validate_columns_in_query(query, df_info['columns'])
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, df_info, sheet_name)
        
        try:
            response = self._call_ollama(system_prompt, user_prompt)
            result = json.loads(response)
            
            if "code" not in result:
                raise ValueError("Response missing code field")
            
            return {
                "success": True,
                "code": result.get("code", ""),
                "explanation": result.get("explanation", ""),
                "operation_type": result.get("operation_type", "unknown"),
                "creates_new_column": result.get("creates_new_column", False),
                "new_column_name": result.get("new_column_name", None),
                "error": None
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "code": None,
                "explanation": None,
                "operation_type": None,
                "creates_new_column": False,
                "new_column_name": None,
                "error": f"Failed to parse response: {str(e)}"
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
                        "temperature": 0.1,
                        "num_predict": 2000
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json()['message']['content']
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to Ollama. Make sure Ollama is running with 'ollama serve'"
            )
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Query might be too complex.")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _build_system_prompt(self) -> str:
        return """You are a data analyst specializing in pandas operations. Generate executable pandas code for user queries.

CRITICAL RULES:
1. DataFrame variable is 'df' (already loaded, DO NOT reload)
2. ONLY use columns that exist in the provided dataframe info
3. Store final result in 'result' variable
4. Result must be DataFrame, Series, or scalar value
5. Use vectorized operations, no loops
6. Handle missing data with .fillna() or .dropna()
7. NEVER use file I/O, imports (except pd/np/datetime), or dangerous operations
8. ALWAYS add .reset_index() after groupby operations
9. For division operations: create new column in df, then set result = df
10. For count operations: use .size() or count existing columns, NEVER make up column names
11. For pivot tables: DO NOT rename columns after multi-column pivot
12. For unpivot: use pd.melt on the FULL dataframe with correct id_vars and value_vars

SUPPORTED OPERATIONS:

MATH: Add, subtract, multiply, divide columns
Example: df['total'] = df['price'] * df['quantity']; result = df

AGGREGATION: sum, mean, median, min, max, count, std
Example: result = df.groupby('category')['sales'].agg(['sum', 'mean']).reset_index()
COUNT Example: result = df.groupby('city').size().reset_index(name='count')

FILTER: Conditional filtering with &, |, .isin(), .str.contains()
Example: result = df[(df['age'] > 25) & (df['salary'] > 50000)]

DATES: Convert, extract components, calculate differences
Example: df['year'] = pd.to_datetime(df['date']).dt.year; result = df

PIVOT: Create pivot tables
Example: result = df.pivot_table(values='sales', index='region', columns='product', aggfunc='sum')
DO NOT rename columns after pivot if columns parameter creates multiple columns

UNPIVOT: Melt operation
Example: result = pd.melt(df, id_vars=['id', 'name'], value_vars=['col1', 'col2'], var_name='variable', value_name='value')

SORT: Sort by columns
Example: result = df.sort_values(by=['dept', 'salary'], ascending=[True, False])

TEXT: String operations, sentiment classification
Example: df['sentiment'] = df['text'].apply(lambda x: 'positive' if 'good' in str(x).lower() else 'negative'); result = df

RESPONSE FORMAT (JSON):
{
    "code": "# Pandas code\\nresult = df.groupby('column').mean().reset_index()",
    "explanation": "Brief explanation",
    "operation_type": "math|aggregation|filter|date|pivot|unpivot|sort|text|other",
    "creates_new_column": true/false,
    "new_column_name": "column_name or null"
}

CRITICAL EXAMPLES:

Query: "Calculate monthly salary by dividing salary by 12"
{
    "code": "df['monthly_salary'] = df['salary'] / 12\\nresult = df",
    "explanation": "Creates monthly_salary column by dividing salary by 12",
    "operation_type": "math",
    "creates_new_column": true,
    "new_column_name": "monthly_salary"
}

Query: "Count number of employees in each city"
{
    "code": "result = df.groupby('city').size().reset_index(name='employee_count')",
    "explanation": "Counts employees per city using size()",
    "operation_type": "aggregation",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Create pivot table with department as rows, city as columns, and average salary as values"
{
    "code": "result = df.pivot_table(values='salary', index='department', columns='city', aggfunc='mean').reset_index()",
    "explanation": "Creates pivot with department rows and city columns",
    "operation_type": "pivot",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Unpivot the data keeping id and name as identifiers and converting salary, age, projects_completed into separate rows"
{
    "code": "result = pd.melt(df, id_vars=['id', 'name'], value_vars=['salary', 'age', 'projects_completed'], var_name='attribute', value_name='value')",
    "explanation": "Converts wide format to long format",
    "operation_type": "unpivot",
    "creates_new_column": false,
    "new_column_name": null
}

Generate safe, executable pandas code. Return only valid JSON."""
    
    def _build_user_prompt(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str
    ) -> str:
        
        columns_info = "\n".join([
            f"  - {col} ({dtype})" 
            for col, dtype in zip(df_info['columns'], df_info['dtypes'])
        ])
        
        sample_data = df_info.get('sample_data', 'Not available')
        stats = df_info.get('statistics', 'Not available')
        
        null_summary = df_info.get('null_counts', {})
        null_info = "\n".join([
            f"  - {col}: {count} nulls" 
            for col, count in null_summary.items() if count > 0
        ])
        if not null_info:
            null_info = "  No null values"
        
        return f"""USER QUERY: {query}

DATAFRAME INFO:
Variable: {sheet_name}
Shape: {df_info['shape'][0]} rows × {df_info['shape'][1]} columns

AVAILABLE COLUMNS (USE ONLY THESE):
{columns_info}

CRITICAL: You must ONLY use the columns listed above. Do not make up or hallucinate column names.

NULL VALUES:
{null_info}

SAMPLE DATA:
{sample_data}

STATISTICS:
{stats}

Generate pandas code to answer the query. Use ONLY the columns listed above. Return only JSON with code, explanation, and operation_type."""
    
    def validate_and_enhance_code(self, code: str) -> str:
        
        forbidden_keywords = [
            'eval', 'exec', 'compile', '__import__', 
            'open', 'file', 'input', 'os.', 'sys.',
            'subprocess', 'socket', 'requests', 'urllib',
            'pickle', 'shelve', 'marshal'
        ]
        
        code_lower = code.lower()
        for keyword in forbidden_keywords:
            if keyword.lower() in code_lower:
                raise ValueError(
                    f"Forbidden operation: '{keyword}'. Code cannot contain file I/O or system calls."
                )
        
        allowed_imports = ['import pandas as pd', 'import numpy as np', 'from datetime import']
        
        lines = code.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                if not any(allowed in line for allowed in allowed_imports):
                    raise ValueError(
                        f"Unauthorized import: {line}. Only pandas, numpy, and datetime allowed."
                    )
        
        if 'result' not in code and 'result =' not in code:
            raise ValueError(
                "Code must assign to 'result' variable. Example: result = df.mean()"
            )
        
        return code
    
    def analyze_unstructured_text(
        self,
        text_data: pd.Series,
        analysis_type: str = "sentiment"
    ) -> pd.Series:
        
        if analysis_type == "sentiment":
            positive_words = [
                'good', 'great', 'excellent', 'amazing', 'wonderful',
                'fantastic', 'awesome', 'satisfied', 'happy', 'love',
                'best', 'perfect', 'outstanding'
            ]
            negative_words = [
                'bad', 'poor', 'terrible', 'awful', 'horrible',
                'disappointed', 'worst', 'hate', 'useless', 'waste',
                'defective', 'broken', 'failure'
            ]
            
            def classify(text):
                text_lower = str(text).lower()
                pos_count = sum(1 for word in positive_words if word in text_lower)
                neg_count = sum(1 for word in negative_words if word in text_lower)
                
                if pos_count > neg_count:
                    return 'positive'
                elif neg_count > pos_count:
                    return 'negative'
                else:
                    return 'neutral'
            
            return text_data.apply(classify)
        else:
            return text_data.apply(lambda x: len(str(x)))