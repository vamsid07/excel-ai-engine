import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import io
from datetime import datetime, timedelta
import traceback


class ExcelService:
    
    def __init__(self):
        self.max_sample_rows = 3
        self.max_result_rows = 10000
    
    def read_excel(
        self, 
        filepath: str, 
        sheet_name: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        
        try:
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
                sheet_name = 'CSV'
            else:
                if sheet_name:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                else:
                    df = pd.read_excel(filepath)
            
            metadata = self._extract_dataframe_info(df)
            metadata['filepath'] = filepath
            metadata['sheet_name'] = sheet_name or 'default'
            
            return df, metadata
            
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")
    
    def list_sheets(self, filepath: str) -> list:
        try:
            if filepath.endswith('.csv'):
                return ['CSV']
            xl_file = pd.ExcelFile(filepath)
            return xl_file.sheet_names
        except Exception as e:
            raise ValueError(f"Error reading file sheets: {str(e)}")
    
    def _extract_dataframe_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        
        sample_df = df.head(5)
        sample_str = sample_df.to_string(index=False)
        
        try:
            stats_df = df.describe()
            stats_str = stats_df.to_string()
        except:
            stats_str = "Statistics not available"
        
        return {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': [str(dtype) for dtype in df.dtypes],
            'sample_data': sample_str,
            'statistics': stats_str,
            'memory_usage': df.memory_usage(deep=True).sum(),
            'null_counts': df.isnull().sum().to_dict(),
            'has_duplicates': df.duplicated().any()
        }
    
    def execute_query_code(
        self, 
        df: pd.DataFrame, 
        code: str
    ) -> Dict[str, Any]:
        
        try:
            namespace = {
                'df': df.copy(),
                'pd': pd,
                'np': np,
                'datetime': datetime,
                'timedelta': timedelta,
                'result': None
            }
            
            exec(code, namespace)
            
            result = namespace.get('result')
            
            if result is None:
                return {
                    'success': False,
                    'error': 'Code did not produce result. Ensure result variable is set.',
                    'result': None,
                    'result_type': None
                }
            
            return self._process_result(result, namespace['df'])
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution error: {str(e)}\n{traceback.format_exc()}",
                'result': None,
                'result_type': None
            }
    
    def _process_result(
        self, 
        result: Any, 
        modified_df: pd.DataFrame
    ) -> Dict[str, Any]:
        
        result_type = type(result).__name__
        
        if isinstance(result, pd.DataFrame):
            result = result.replace([float('inf'), float('-inf')], None)
            result = result.where(pd.notna(result), None)
            
            if len(result) > self.max_result_rows:
                result = result.head(self.max_result_rows)
                truncated = True
            else:
                truncated = False
            
            return {
                'success': True,
                'result': result.to_dict(orient='records'),
                'result_type': 'dataframe',
                'shape': result.shape,
                'columns': result.columns.tolist(),
                'truncated': truncated,
                'error': None
            }
        
        elif isinstance(result, pd.Series):
            result = result.replace([float('inf'), float('-inf')], None)
            result = result.where(pd.notna(result), None)
            
            return {
                'success': True,
                'result': result.to_dict(),
                'result_type': 'series',
                'shape': (len(result),),
                'error': None
            }
        
        elif isinstance(result, (int, float, str, bool)):
            if isinstance(result, float):
                if pd.isna(result) or result == float('inf') or result == float('-inf'):
                    result = None
            
            return {
                'success': True,
                'result': result,
                'result_type': 'scalar',
                'value_type': result_type,
                'error': None
            }
        
        elif isinstance(result, dict):
            return {
                'success': True,
                'result': result,
                'result_type': 'dict',
                'error': None
            }
        
        elif isinstance(result, list):
            return {
                'success': True,
                'result': result,
                'result_type': 'list',
                'length': len(result),
                'error': None
            }
        
        else:
            return {
                'success': True,
                'result': str(result),
                'result_type': 'other',
                'original_type': result_type,
                'error': None
            }
    
    def save_dataframe(
        self, 
        df: pd.DataFrame, 
        filepath: str,
        sheet_name: str = 'Result'
    ) -> str:
        
        try:
            df.to_excel(filepath, sheet_name=sheet_name, index=False)
            return filepath
        except Exception as e:
            raise ValueError(f"Error saving Excel file: {str(e)}")
    
    def merge_dataframes(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        join_type: str = 'inner',
        left_on: str = None,
        right_on: str = None
    ) -> pd.DataFrame:
        
        try:
            return pd.merge(
                df1, 
                df2, 
                how=join_type,
                left_on=left_on,
                right_on=right_on
            )
        except Exception as e:
            raise ValueError(f"Error merging DataFrames: {str(e)}")