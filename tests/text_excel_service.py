import pytest
import pandas as pd
import numpy as np
from app.services.excel_service import ExcelService
from pathlib import Path


class TestExcelService:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = ExcelService()
    
    def test_read_excel_success(self, sample_excel_file):
        df, metadata = self.service.read_excel(sample_excel_file)
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert metadata['shape'][0] == 100
        assert 'columns' in metadata
        assert 'dtypes' in metadata
        assert 'filepath' in metadata
    
    def test_read_excel_with_sheet_name(self, sample_excel_file):
        df, metadata = self.service.read_excel(sample_excel_file, sheet_name='TestSheet')
        
        assert isinstance(df, pd.DataFrame)
        assert metadata['sheet_name'] == 'TestSheet'
    
    def test_read_excel_nonexistent_file(self):
        with pytest.raises(ValueError, match="Error reading file"):
            self.service.read_excel("nonexistent_file.xlsx")
    
    def test_list_sheets(self, sample_excel_file):
        sheets = self.service.list_sheets(sample_excel_file)
        
        assert isinstance(sheets, list)
        assert len(sheets) > 0
        assert 'TestSheet' in sheets
    
    def test_extract_dataframe_info(self, sample_dataframe):
        info = self.service._extract_dataframe_info(sample_dataframe)
        
        assert 'shape' in info
        assert 'columns' in info
        assert 'dtypes' in info
        assert 'sample_data' in info
        assert 'statistics' in info
        assert 'memory_usage' in info
        assert 'null_counts' in info
        assert 'has_duplicates' in info
    
    def test_execute_query_code_dataframe_result(self, sample_dataframe):
        code = "result = df[df['salary'] > 50000]"
        result = self.service.execute_query_code(sample_dataframe, code)
        
        assert result['success'] is True
        assert result['result_type'] == 'dataframe'
        assert isinstance(result['result'], list)
        assert 'shape' in result
        assert 'columns' in result
    
    def test_execute_query_code_scalar_result(self, sample_dataframe):
        code = "result = df['salary'].mean()"
        result = self.service.execute_query_code(sample_dataframe, code)
        
        assert result['success'] is True
        assert result['result_type'] == 'scalar'
        assert isinstance(result['result'], (int, float))
    
    def test_execute_query_code_series_result(self, sample_dataframe):
        code = "result = df['salary']"
        result = self.service.execute_query_code(sample_dataframe, code)
        
        assert result['success'] is True
        assert result['result_type'] == 'series'
        assert isinstance(result['result'], dict)
    
    def test_execute_query_code_no_result(self, sample_dataframe):
        code = "x = df['salary'].mean()"
        result = self.service.execute_query_code(sample_dataframe, code)
        
        assert result['success'] is False
        assert 'result variable is set' in result['error']
    
    def test_execute_query_code_syntax_error(self, sample_dataframe):
        code = "result = df['salary'].mean("
        result = self.service.execute_query_code(sample_dataframe, code)
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_execute_query_code_truncation(self, sample_dataframe):
        large_df = pd.concat([sample_dataframe] * 150, ignore_index=True)
        code = "result = df"
        
        result = self.service.execute_query_code(large_df, code)
        
        assert result['success'] is True
        assert result['truncated'] is True
        assert len(result['result']) == self.service.max_result_rows
    
    def test_process_result_dataframe(self, sample_dataframe):
        result = self.service._process_result(sample_dataframe, sample_dataframe)
        
        assert result['success'] is True
        assert result['result_type'] == 'dataframe'
        assert isinstance(result['result'], list)
    
    def test_process_result_handles_inf(self):
        df = pd.DataFrame({'a': [1, float('inf'), 3]})
        result = self.service._process_result(df, df)
        
        assert result['success'] is True
        assert result['result'][1]['a'] is None
    
    def test_process_result_handles_nan(self):
        df = pd.DataFrame({'a': [1, np.nan, 3]})
        result = self.service._process_result(df, df)
        
        assert result['success'] is True
        assert result['result'][1]['a'] is None
    
    def test_save_dataframe_excel(self, sample_dataframe, test_data_dir):
        filepath = test_data_dir / "output.xlsx"
        result_path = self.service.save_dataframe(sample_dataframe, str(filepath))
        
        assert Path(result_path).exists()
        
        df_read = pd.read_excel(result_path)
        assert len(df_read) == len(sample_dataframe)
    
    def test_save_dataframe_csv(self, sample_dataframe, test_data_dir):
        filepath = test_data_dir / "output.csv"
        result_path = self.service.save_dataframe(sample_dataframe, str(filepath))
        
        assert Path(result_path).exists()
        
        df_read = pd.read_csv(result_path)
        assert len(df_read) == len(sample_dataframe)
    
    def test_merge_dataframes_with_columns(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.merge_dataframes(df1, df2, 'inner', 'id', 'id')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_merge_dataframes_common_columns(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.merge_dataframes(df1, df2, 'inner')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    
    def test_merge_dataframes_no_common_columns(self):
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'b': [4, 5, 6]})
        
        with pytest.raises(ValueError, match="No common columns"):
            self.service.merge_dataframes(df1, df2)
    
    def test_merge_dataframes_left_join(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.merge_dataframes(df1, df2, 'left', 'id', 'id')
        
        assert len(result) == len(df1)
    
    def test_merge_dataframes_outer_join(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.merge_dataframes(df1, df2, 'outer', 'id', 'id')
        
        assert len(result) >= max(len(df1), len(df2))