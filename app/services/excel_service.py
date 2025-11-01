import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional
import io
from datetime import datetime, timedelta
import traceback


class ExcelService:
    
    def __init__(self):
        self.max_sample_rows = 5
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
            
            if df.empty:
                raise ValueError("DataFrame is empty after reading file")
            
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
        sample_str = sample_df.to_string(index=False, max_cols=20)
        
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                stats_df = df[numeric_cols].describe()
                stats_str = stats_df.to_string()
            else:
                stats_str = "No numeric columns for statistics"
        except Exception:
            stats_str = "Statistics not available"
        
        return {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': [str(dtype) for dtype in df.dtypes],
            'sample_data': sample_str,
            'statistics': stats_str,
            'memory_usage': int(df.memory_usage(deep=True).sum()),
            'null_counts': df.isnull().sum().to_dict(),
            'has_duplicates': bool(df.duplicated().any())
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
            error_details = traceback.format_exc()
            return {
                'success': False,
                'error': f"Execution error: {str(e)}",
                'error_details': error_details,
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
            
            truncated = False
            if len(result) > self.max_result_rows:
                result = result.head(self.max_result_rows)
                truncated = True
            
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
        
        elif isinstance(result, (int, float, str, bool, np.integer, np.floating)):
            if isinstance(result, (float, np.floating)):
                if pd.isna(result) or result == float('inf') or result == float('-inf'):
                    result = None
                else:
                    result = float(result)
            elif isinstance(result, (int, np.integer)):
                result = int(result)
            
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
        
        elif isinstance(result, (list, tuple)):
            return {
                'success': True,
                'result': list(result),
                'result_type': 'list',
                'length': len(result),
                'error': None
            }
        
        else:
            try:
                result_str = str(result)
                return {
                    'success': True,
                    'result': result_str,
                    'result_type': 'other',
                    'original_type': result_type,
                    'error': None
                }
            except Exception:
                return {
                    'success': False,
                    'error': f'Cannot serialize result of type {result_type}',
                    'result': None,
                    'result_type': None
                }
    
    def save_dataframe(
        self, 
        df: pd.DataFrame, 
        filepath: str,
        sheet_name: str = 'Result'
    ) -> str:
        
        try:
            if filepath.endswith('.csv'):
                df.to_csv(filepath, index=False)
            else:
                df.to_excel(filepath, sheet_name=sheet_name, index=False)
            return filepath
        except Exception as e:
            raise ValueError(f"Error saving file: {str(e)}")
    
    def merge_dataframes(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        join_type: str = 'inner',
        left_on: str = None,
        right_on: str = None
    ) -> pd.DataFrame:
        
        try:
            if left_on and right_on:
                return pd.merge(
                    df1, 
                    df2, 
                    how=join_type,
                    left_on=left_on,
                    right_on=right_on,
                    suffixes=('_left', '_right')
                )
            else:
                common_cols = list(set(df1.columns) & set(df2.columns))
                if not common_cols:
                    raise ValueError("No common columns found for join")
                return pd.merge(
                    df1,
                    df2,
                    how=join_type,
                    on=common_cols[0],
                    suffixes=('_left', '_right')
                )
        except Exception as e:
            raise ValueError(f"Error merging DataFrames: {str(e)}")