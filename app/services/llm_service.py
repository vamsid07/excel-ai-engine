from app.core.config import settings
import json
from typing import Dict, Any, Optional
import pandas as pd
import requests


class LLMService:
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
        self.model = getattr(settings, 'OLLAMA_MODEL', 'llama3.2')
    
    def generate_pandas_code(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str = "df"
    ) -> Dict[str, Any]:
        
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

REQUIREMENTS:
1. DataFrame variable is 'df' (already loaded)
2. Only pandas and numpy operations allowed
3. Store final result in 'result' variable
4. Result must be DataFrame, Series, or scalar value
5. Use vectorized operations, avoid loops
6. Handle missing data appropriately
7. No file I/O, imports (except pd/np/datetime), or dangerous operations
8. Add .reset_index() after groupby operations
9. Handle errors (division by zero, missing columns, type issues)

SUPPORTED OPERATIONS:

MATH: Add, subtract, multiply, divide columns
Example: df['total'] = df['price'] * df['quantity']

AGGREGATION: sum, mean, median, min, max, count, std
Example: df.groupby('category')['sales'].agg(['sum', 'mean']).reset_index()

FILTER: Conditional filtering with &, |, .isin(), .str.contains()
Example: df[(df['age'] > 25) & (df['salary'] > 50000)]

DATES: Convert, extract components, calculate differences
Example: df['year'] = pd.to_datetime(df['date']).dt.year

PIVOT: Create pivot tables
Example: df.pivot_table(values='sales', index='region', columns='product', aggfunc='sum')

UNPIVOT: Melt operation
Example: df.melt(id_vars=['id'], value_vars=['col1', 'col2'])

SORT: Sort by columns
Example: df.sort_values(by=['dept', 'salary'], ascending=[True, False])

JOIN: Merge dataframes
Example: pd.merge(df1, df2, on='key', how='inner')

TEXT: String operations, sentiment classification
Example: df['sentiment'] = df['text'].apply(lambda x: 'positive' if 'good' in str(x).lower() else 'negative')

RESPONSE FORMAT (JSON):
{
    "code": "# Pandas code\\nresult = df.groupby('column').mean()",
    "explanation": "Brief explanation",
    "operation_type": "math|aggregation|filter|date|pivot|unpivot|join|text|other",
    "creates_new_column": true/false,
    "new_column_name": "column_name or null"
}

EXAMPLES:

Query: "Add salary and bonus columns"
{
    "code": "df['total_comp'] = df['salary'] + df['bonus']\\nresult = df",
    "explanation": "Creates total_comp by adding salary and bonus",
    "operation_type": "math",
    "creates_new_column": true,
    "new_column_name": "total_comp"
}

Query: "Average salary by department"
{
    "code": "result = df.groupby('department')['salary'].mean().reset_index()\\nresult.columns = ['department', 'avg_salary']",
    "explanation": "Groups by department and calculates mean salary",
    "operation_type": "aggregation",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Filter salary over 50000"
{
    "code": "result = df[df['salary'] > 50000]",
    "explanation": "Filters rows where salary exceeds 50000",
    "operation_type": "filter",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Extract year from date"
{
    "code": "from datetime import datetime\\ndf['year'] = pd.to_datetime(df['date']).dt.year\\nresult = df",
    "explanation": "Extracts year component from date column",
    "operation_type": "date",
    "creates_new_column": true,
    "new_column_name": "year"
}

Query: "Pivot by department and city"
{
    "code": "result = df.pivot_table(values='salary', index='department', columns='city', aggfunc='mean').reset_index()",
    "explanation": "Creates pivot with departments as rows and cities as columns",
    "operation_type": "pivot",
    "creates_new_column": false,
    "new_column_name": null
}

Query: "Classify feedback sentiment"
{
    "code": "positive_words = ['good', 'great', 'excellent']\\nnegative_words = ['bad', 'poor', 'terrible']\\ndef classify(text):\\n    text_lower = str(text).lower()\\n    if any(word in text_lower for word in positive_words):\\n        return 'positive'\\n    elif any(word in text_lower for word in negative_words):\\n        return 'negative'\\n    return 'neutral'\\ndf['sentiment'] = df['feedback'].apply(classify)\\nresult = df",
    "explanation": "Classifies feedback as positive, negative, or neutral",
    "operation_type": "text",
    "creates_new_column": true,
    "new_column_name": "sentiment"
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

COLUMNS:
{columns_info}

NULL VALUES:
{null_info}

SAMPLE DATA:
{sample_data}

STATISTICS:
{stats}

Generate pandas code to answer the query. Return only JSON with code, explanation, and operation_type."""
    
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