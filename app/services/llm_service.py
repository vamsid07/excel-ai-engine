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
        return """You are an expert pandas code generator. Generate safe, executable pandas code for data analysis queries.

CRITICAL RULES - MUST FOLLOW:
1. DataFrame variable is ALWAYS 'df' (already loaded)
2. ONLY use columns that exist in the provided schema
3. ALWAYS store final result in 'result' variable
4. Result must be DataFrame, Series, or scalar
5. Use vectorized operations only
6. Handle NaN with .fillna() or .dropna()
7. NO file I/O, NO dangerous operations
8. ALWAYS use .reset_index() after groupby
9. For NEW COLUMNS: modify df then assign result = df
10. For COUNTS: use .size() with reset_index(name='count_column_name')
11. For PIVOTS: DO NOT rename columns after pivot_table
12. For UNPIVOT: use pd.melt() on FULL df with all id_vars and value_vars

OPERATION PATTERNS:

MATH (Create New Column):
Query: "divide salary by 12"
Code:
df['monthly_salary'] = df['salary'] / 12
result = df

Query: "add salary and bonus"
Code:
df['total'] = df['salary'] + df['bonus']
result = df

AGGREGATION:
Query: "average salary by department"
Code:
result = df.groupby('department')['salary'].mean().reset_index()

Query: "count employees by city"
Code:
result = df.groupby('city').size().reset_index(name='employee_count')

Query: "sum, mean, min, max salary by dept"
Code:
result = df.groupby('department')['salary'].agg(['sum', 'mean', 'min', 'max']).reset_index()

FILTER:
Query: "salary > 100000"
Code:
result = df[df['salary'] > 100000]

Query: "age > 30 AND salary > 50000"
Code:
result = df[(df['age'] > 30) & (df['salary'] > 50000)]

Query: "city contains 'New'"
Code:
result = df[df['city'].str.contains('New', na=False)]

DATE OPERATIONS:
Query: "extract year from join_date"
Code:
df['join_year'] = pd.to_datetime(df['join_date']).dt.year
result = df

Query: "extract month and day"
Code:
df['month'] = pd.to_datetime(df['join_date']).dt.month
df['day'] = pd.to_datetime(df['join_date']).dt.day
result = df

Query: "years from join_date to today"
Code:
df['years_service'] = (pd.Timestamp.now() - pd.to_datetime(df['join_date'])).dt.days / 365.25
result = df

PIVOT:
Query: "pivot dept vs avg salary"
Code:
result = df.pivot_table(values='salary', index='department', aggfunc='mean').reset_index()

Query: "pivot dept as rows, city as cols, avg salary"
Code:
result = df.pivot_table(values='salary', index='department', columns='city', aggfunc='mean').reset_index()

UNPIVOT:
Query: "unpivot keeping id, name and melt salary, age"
Code:
result = pd.melt(df, id_vars=['id', 'name'], value_vars=['salary', 'age'], var_name='attribute', value_name='value')

TEXT:
Query: "classify feedback as positive/negative"
Code:
def classify_sentiment(text):
    text_lower = str(text).lower()
    positive_words = ['good', 'great', 'excellent', 'satisfied', 'happy', 'love']
    negative_words = ['bad', 'poor', 'terrible', 'disappointed', 'hate', 'worst']
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    return 'neutral'

df['sentiment'] = df['feedback_column'].apply(classify_sentiment)
result = df

SORTING:
Query: "top 10 by salary"
Code:
result = df.nlargest(10, 'salary')

Query: "sort by dept asc, salary desc"
Code:
result = df.sort_values(by=['department', 'salary'], ascending=[True, False])

JSON RESPONSE FORMAT:
{
    "code": "# Valid pandas code here\\nresult = ...",
    "explanation": "Brief explanation of what the code does",
    "operation_type": "math|aggregation|filter|date|pivot|unpivot|sort|text|other",
    "creates_new_column": true or false,
    "new_column_name": "column_name" or null
}

VALIDATION CHECKLIST:
✓ Does code use only columns from schema?
✓ Is result variable assigned?
✓ Are all operations vectorized?
✓ Is reset_index() used after groupby?
✓ For new columns: does it end with result = df?
✓ For counts: does it use .size().reset_index(name='...')?
✓ No column renaming after multi-column pivot?

Generate clean, working pandas code. Return ONLY valid JSON."""
    
    def _build_user_prompt(
        self, 
        query: str, 
        df_info: Dict[str, Any],
        sheet_name: str
    ) -> str:
        
        columns_info = "\n".join([
            f"  - {col} (type: {dtype})" 
            for col, dtype in zip(df_info['columns'], df_info['dtypes'])
        ])
        
        sample_data = df_info.get('sample_data', 'Not available')
        
        null_summary = df_info.get('null_counts', {})
        null_info = "\n".join([
            f"  - {col}: {count} nulls" 
            for col, count in null_summary.items() if count > 0
        ])
        if not null_info:
            null_info = "  No null values"
        
        return f"""Generate pandas code for this query.

USER QUERY: {query}

DATAFRAME SCHEMA:
Variable name: {sheet_name}
Shape: {df_info['shape'][0]} rows × {df_info['shape'][1]} columns

AVAILABLE COLUMNS (use ONLY these exact names):
{columns_info}

NULL VALUES:
{null_info}

SAMPLE DATA (first 5 rows):
{sample_data}

INSTRUCTIONS:
1. Use ONLY the columns listed above
2. Assign final result to 'result' variable
3. For new columns: modify df then set result = df
4. For counts: use .size().reset_index(name='descriptive_name')
5. For date operations: always assign result = df at the end
6. Return ONLY valid JSON with code, explanation, operation_type

Generate the pandas code now."""
    
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