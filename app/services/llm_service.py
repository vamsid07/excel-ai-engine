"""
Enhanced LLM Service for intelligent query interpretation and code generation
Optimized for all required operations with comprehensive error handling
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
        
        system_prompt = self._create_comprehensive_system_prompt()
        user_prompt = self._create_user_prompt(query, df_info, sheet_name)
        
        try:
            if self.use_ollama:
                response = self._call_ollama(system_prompt, user_prompt)
            else:
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
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "code": None,
                "explanation": None,
                "operation_type": None,
                "creates_new_column": False,
                "new_column_name": None,
                "error": f"Failed to parse LLM response as JSON: {str(e)}"
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
                "Cannot connect to Ollama. Make sure Ollama is running: 'ollama serve'"
            )
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out. Query might be too complex.")
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def _create_comprehensive_system_prompt(self) -> str:
        """Create enhanced system prompt for all required operations"""
        return """You are an expert data analyst and Python programmer specializing in pandas operations.
Your task is to generate SAFE, EXECUTABLE pandas code to answer user queries about Excel data.

=== CRITICAL RULES ===
1. The DataFrame variable is named 'df' (already loaded, do NOT read files)
2. Generate ONLY pandas/numpy code - NO file I/O, NO imports except pd/np
3. ALWAYS store the final result in a variable called 'result'
4. The result MUST be a DataFrame, Series, or simple value (int, float, str, dict, list)
5. Use vectorized operations - AVOID loops when possible
6. Handle missing data appropriately (use .dropna(), .fillna(), or handle NaN in operations)
7. For aggregations, return a DataFrame with meaningful column names
8. For filtering, return the filtered DataFrame
9. For new columns, modify df and set result = df
10. NEVER use eval(), exec(), __import__(), open(), os., sys., subprocess
11. Keep code clean, efficient, and well-commented
12. Always use .reset_index() after groupby operations to create clean DataFrames
13. Handle potential errors (division by zero, missing columns, type mismatches)

=== SUPPORTED OPERATIONS ===

1. BASIC MATH OPERATIONS
   - Addition, subtraction, multiplication, division on columns
   - Create new columns with calculations
   - Example: df['total'] = df['price'] * df['quantity']
   
2. AGGREGATIONS
   - sum(), mean(), median(), min(), max(), count(), std(), var()
   - Group by operations with aggregations
   - Example: df.groupby('category')['sales'].agg(['sum', 'mean', 'count']).reset_index()

3. FILTERING
   - Filter rows based on conditions (>, <, ==, !=, .isin(), .str.contains())
   - Multiple conditions with & (and) | (or)
   - Example: df[(df['age'] > 25) & (df['salary'] > 50000)]

4. DATE OPERATIONS
   - Convert to datetime: pd.to_datetime(df['date_column'])
   - Extract components: .dt.year, .dt.month, .dt.day, .dt.dayofweek
   - Date differences: (df['end_date'] - df['start_date']).dt.days
   - Example: df['year'] = pd.to_datetime(df['date']).dt.year

5. PIVOT OPERATIONS
   - Create pivot table: df.pivot_table(values='sales', index='region', columns='product', aggfunc='sum')
   - Unpivot/melt: df.melt(id_vars=['id'], value_vars=['col1', 'col2'])

6. SORTING
   - Sort by single/multiple columns
   - Example: df.sort_values(by=['department', 'salary'], ascending=[True, False])

7. JOINING (if multiple DataFrames are mentioned)
   - Use pd.merge() for joins
   - Example: pd.merge(df1, df2, on='key', how='inner')

8. TEXT OPERATIONS (for unstructured data)
   - String operations: .str.lower(), .str.upper(), .str.contains()
   - Split/extract: .str.split(), .str.extract()
   - Example: df['sentiment'] = df['text'].apply(lambda x: 'positive' if 'good' in str(x).lower() else 'negative')

=== ERROR HANDLING ===
- Check if columns exist before using them
- Handle potential division by zero
- Convert data types when necessary (e.g., pd.to_numeric(df['col'], errors='coerce'))
- Use try-except for risky operations when appropriate

=== RESPONSE FORMAT (STRICT JSON) ===
{
    "code": "# Your pandas code here\\nresult = df.groupby('column').mean()",
    "explanation": "Brief explanation of what the code does",
    "operation_type": "math|aggregation|filter|date|pivot|unpivot|join|text|other",
    "creates_new_column": true/false,
    "new_column_name": "column_name or null"
}

=== EXAMPLES ===

Example 1 - Basic Math:
Query: "Add a column for total_compensation which is salary plus bonus"
Response:
{
    "code": "# Calculate total compensation\\ndf['total_compensation'] = df['salary'] + df['bonus']\\nresult = df",
    "explanation": "Creates a new column 'total_compensation' by adding salary and bonus columns",
    "operation_type": "math",
    "creates_new_column": true,
    "new_column_name": "total_compensation"
}

Example 2 - Aggregation:
Query: "Calculate average salary by department"
Response:
{
    "code": "# Group by department and calculate mean salary\\nresult = df.groupby('department')['salary'].mean().reset_index()\\nresult.columns = ['department', 'average_salary']",
    "explanation": "Groups data by department and calculates the average salary for each department",
    "operation_type": "aggregation",
    "creates_new_column": false,
    "new_column_name": null
}

Example 3 - Filtering:
Query: "Show employees earning more than 50000 in Engineering department"
Response:
{
    "code": "# Filter for Engineering employees with salary > 50000\\nresult = df[(df['department'] == 'Engineering') & (df['salary'] > 50000)]",
    "explanation": "Filters the dataset to show only Engineering employees with salary greater than 50000",
    "operation_type": "filter",
    "creates_new_column": false,
    "new_column_name": null
}

Example 4 - Date Operations:
Query: "Extract year from join_date and calculate years of service"
Response:
{
    "code": "# Extract year and calculate service years\\nfrom datetime import datetime\\ndf['join_year'] = pd.to_datetime(df['join_date']).dt.year\\ncurrent_year = datetime.now().year\\ndf['years_of_service'] = current_year - df['join_year']\\nresult = df",
    "explanation": "Extracts the year from join_date column and calculates years of service by subtracting from current year",
    "operation_type": "date",
    "creates_new_column": true,
    "new_column_name": "join_year, years_of_service"
}

Example 5 - Pivot:
Query: "Create pivot table showing average salary by department and city"
Response:
{
    "code": "# Create pivot table\\nresult = df.pivot_table(values='salary', index='department', columns='city', aggfunc='mean').reset_index()",
    "explanation": "Creates a pivot table with departments as rows, cities as columns, and average salary as values",
    "operation_type": "pivot",
    "creates_new_column": false,
    "new_column_name": null
}

Example 6 - Unpivot:
Query: "Unpivot the sales data from wide to long format"
Response:
{
    "code": "# Unpivot/melt the DataFrame\\nid_cols = [col for col in df.columns if col not in ['Q1', 'Q2', 'Q3', 'Q4']]\\nresult = df.melt(id_vars=id_cols, var_name='Quarter', value_name='Sales')",
    "explanation": "Transforms the DataFrame from wide format to long format, converting quarter columns into rows",
    "operation_type": "unpivot",
    "creates_new_column": false,
    "new_column_name": null
}

Example 7 - Text Analysis (Simple):
Query: "Analyze customer feedback and classify as positive or negative"
Response:
{
    "code": "# Simple sentiment classification\\npositive_words = ['good', 'great', 'excellent', 'amazing', 'satisfied']\\nnegative_words = ['bad', 'poor', 'terrible', 'disappointed', 'worse']\\n\\ndef classify_sentiment(text):\\n    text_lower = str(text).lower()\\n    if any(word in text_lower for word in positive_words):\\n        return 'positive'\\n    elif any(word in text_lower for word in negative_words):\\n        return 'negative'\\n    else:\\n        return 'neutral'\\n\\ndf['sentiment'] = df['feedback'].apply(classify_sentiment)\\nresult = df",
    "explanation": "Classifies customer feedback as positive, negative, or neutral based on keyword matching",
    "operation_type": "text",
    "creates_new_column": true,
    "new_column_name": "sentiment"
}

Example 8 - Multiple Aggregations:
Query: "Show sum, average, min, max of sales by region"
Response:
{
    "code": "# Multiple aggregations\\nresult = df.groupby('region')['sales'].agg([\\n    ('total_sales', 'sum'),\\n    ('average_sales', 'mean'),\\n    ('min_sales', 'min'),\\n    ('max_sales', 'max'),\\n    ('count', 'count')\\n]).reset_index()",
    "explanation": "Groups by region and calculates multiple statistics (sum, mean, min, max, count) for sales",
    "operation_type": "aggregation",
    "creates_new_column": false,
    "new_column_name": null
}

=== IMPORTANT REMINDERS ===
- Always ensure your code is safe and executable
- Test for edge cases (empty DataFrames, missing columns, null values)
- Provide clear, descriptive variable names
- Add comments to explain complex operations
- Return ONLY valid JSON, no extra text or markdown
- Make sure the 'result' variable is always assigned

Generate pandas code that directly answers the user's query. Be precise, efficient, and safe."""
    
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
        stats = df_info.get('statistics', 'Not available')
        
        # Add null count summary
        null_summary = df_info.get('null_counts', {})
        null_info = "\n".join([
            f"  - {col}: {count} nulls" 
            for col, count in null_summary.items() if count > 0
        ])
        if not null_info:
            null_info = "  No null values"
        
        return f"""USER QUERY: {query}

DATAFRAME INFORMATION:
Variable name: {sheet_name}
Shape: {df_info['shape'][0]} rows × {df_info['shape'][1]} columns

COLUMNS AND TYPES:
{columns_info}

NULL VALUES:
{null_info}

SAMPLE DATA (first 3 rows):
{sample_data}

STATISTICS (for numerical columns):
{stats}

INSTRUCTIONS:
1. Analyze the query carefully
2. Identify which columns are needed
3. Generate safe, executable pandas code
4. Handle edge cases (nulls, type conversions, missing columns)
5. Store the final result in 'result' variable
6. Return ONLY valid JSON with code, explanation, and operation_type

Generate the pandas code now. Return ONLY JSON, no markdown or extra text."""
    
    def validate_and_enhance_code(self, code: str) -> str:
        """
        Validate and enhance the generated code for safety
        
        Args:
            code: Generated pandas code
            
        Returns:
            Enhanced and validated code
            
        Raises:
            ValueError: If code contains forbidden operations
        """
        # Remove any potentially dangerous operations
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
                    f"Forbidden operation detected: '{keyword}'. "
                    f"Code cannot contain file I/O, system calls, or network operations."
                )
        
        # Ensure imports are limited
        allowed_imports = ['import pandas as pd', 'import numpy as np', 'from datetime import']
        
        lines = code.split('\n')
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('import ') or line_stripped.startswith('from '):
                if not any(allowed in line for allowed in allowed_imports):
                    raise ValueError(
                        f"Unauthorized import: {line}. "
                        f"Only pandas, numpy, and datetime imports are allowed."
                    )
        
        # Check if 'result' is assigned
        if 'result' not in code and 'result =' not in code:
            raise ValueError(
                "Generated code must assign a value to 'result' variable. "
                "Example: result = df.groupby('column').mean()"
            )
        
        return code
    
    def analyze_unstructured_text(
        self,
        text_data: pd.Series,
        analysis_type: str = "sentiment"
    ) -> pd.Series:
        """
        Simple text analysis without external LLM calls
        
        Args:
            text_data: Series containing text to analyze
            analysis_type: Type of analysis (sentiment, summary, etc.)
            
        Returns:
            Series with analysis results
        """
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
            # Default: return text length as a simple metric
            return text_data.apply(lambda x: len(str(x)))