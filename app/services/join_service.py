"""
Join Service for multi-file operations
"""
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from app.services.excel_service import ExcelService


class JoinService:
    """Service for joining multiple DataFrames"""
    
    def __init__(self):
        self.excel_service = ExcelService()
    
    def load_multiple_files(
        self, 
        filepaths: List[str],
        sheet_names: Optional[List[str]] = None
    ) -> Dict[str, Tuple[pd.DataFrame, Dict[str, Any]]]:
        """
        Load multiple Excel files
        
        Args:
            filepaths: List of file paths
            sheet_names: Optional list of sheet names (one per file)
            
        Returns:
            Dict mapping filepath to (DataFrame, metadata)
        """
        loaded_data = {}
        
        for i, filepath in enumerate(filepaths):
            sheet_name = sheet_names[i] if sheet_names and i < len(sheet_names) else None
            
            try:
                df, metadata = self.excel_service.read_excel(filepath, sheet_name)
                loaded_data[filepath] = (df, metadata)
            except Exception as e:
                raise ValueError(f"Error loading {filepath}: {str(e)}")
        
        return loaded_data
    
    def smart_join(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        join_columns: Optional[List[str]] = None,
        how: str = 'inner'
    ) -> pd.DataFrame:
        """
        Intelligently join two DataFrames
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            join_columns: Columns to join on (auto-detect if None)
            how: Join type (inner, left, right, outer)
            
        Returns:
            Merged DataFrame
        """
        # Auto-detect join columns if not specified
        if join_columns is None:
            join_columns = self._detect_join_columns(df1, df2)
            if not join_columns:
                raise ValueError(
                    "Could not auto-detect join columns. "
                    "Please specify join columns explicitly."
                )
        
        # Validate join columns exist
        for col in join_columns:
            if col not in df1.columns:
                raise ValueError(f"Column '{col}' not found in first dataset")
            if col not in df2.columns:
                raise ValueError(f"Column '{col}' not found in second dataset")
        
        # Perform the join
        try:
            if len(join_columns) == 1:
                result = pd.merge(
                    df1, df2, 
                    on=join_columns[0], 
                    how=how,
                    suffixes=('_left', '_right')
                )
            else:
                result = pd.merge(
                    df1, df2,
                    on=join_columns,
                    how=how,
                    suffixes=('_left', '_right')
                )
            
            return result
            
        except Exception as e:
            raise ValueError(f"Join operation failed: {str(e)}")
    
    def _detect_join_columns(
        self, 
        df1: pd.DataFrame, 
        df2: pd.DataFrame
    ) -> List[str]:
        """
        Auto-detect potential join columns based on common column names
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            List of common column names
        """
        # Find columns with same name
        common_cols = list(set(df1.columns) & set(df2.columns))
        
        if not common_cols:
            return []
        
        # Prioritize columns that look like IDs or keys
        id_keywords = ['id', 'key', 'code', 'number', 'no']
        priority_cols = [
            col for col in common_cols 
            if any(keyword in col.lower() for keyword in id_keywords)
        ]
        
        if priority_cols:
            return priority_cols[:1]  # Return the first ID-like column
        
        return common_cols[:1]  # Return the first common column
    
    def multi_join(
        self,
        dataframes: List[pd.DataFrame],
        join_columns: List[str],
        how: str = 'inner'
    ) -> pd.DataFrame:
        """
        Join multiple DataFrames sequentially
        
        Args:
            dataframes: List of DataFrames to join
            join_columns: Columns to join on
            how: Join type
            
        Returns:
            Final merged DataFrame
        """
        if len(dataframes) < 2:
            raise ValueError("Need at least 2 DataFrames to join")
        
        result = dataframes[0]
        
        for df in dataframes[1:]:
            result = self.smart_join(result, df, join_columns, how)
        
        return result
    
    def concatenate_dataframes(
        self,
        dataframes: List[pd.DataFrame],
        axis: int = 0,
        ignore_index: bool = True
    ) -> pd.DataFrame:
        """
        Concatenate multiple DataFrames vertically or horizontally
        
        Args:
            dataframes: List of DataFrames
            axis: 0 for vertical (rows), 1 for horizontal (columns)
            ignore_index: Whether to reset index
            
        Returns:
            Concatenated DataFrame
        """
        try:
            return pd.concat(dataframes, axis=axis, ignore_index=ignore_index)
        except Exception as e:
            raise ValueError(f"Concatenation failed: {str(e)}")
    
    def analyze_join_potential(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze two DataFrames for join potential
        
        Args:
            df1: First DataFrame
            df2: Second DataFrame
            
        Returns:
            Analysis results
        """
        common_cols = list(set(df1.columns) & set(df2.columns))
        
        analysis = {
            'common_columns': common_cols,
            'recommended_join_columns': self._detect_join_columns(df1, df2),
            'df1_shape': df1.shape,
            'df2_shape': df2.shape,
            'df1_columns': df1.columns.tolist(),
            'df2_columns': df2.columns.tolist()
        }
        
        # Analyze uniqueness of common columns
        if common_cols:
            uniqueness = {}
            for col in common_cols:
                uniqueness[col] = {
                    'df1_unique_ratio': df1[col].nunique() / len(df1),
                    'df2_unique_ratio': df2[col].nunique() / len(df2),
                    'df1_null_count': df1[col].isnull().sum(),
                    'df2_null_count': df2[col].isnull().sum()
                }
            analysis['column_uniqueness'] = uniqueness
        
        return analysis