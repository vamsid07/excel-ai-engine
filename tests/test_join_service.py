import pytest
import pandas as pd
from app.services.join_service import JoinService


class TestJoinService:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = JoinService()
    
    def test_init(self):
        assert self.service.excel_service is not None
    
    def test_smart_join_inner(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.smart_join(df1, df2, ['id'], 'inner')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert 'id' in result.columns
    
    def test_smart_join_left(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.smart_join(df1, df2, ['id'], 'left')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(df1)
    
    def test_smart_join_right(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.smart_join(df1, df2, ['id'], 'right')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(df2)
    
    def test_smart_join_outer(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.smart_join(df1, df2, ['id'], 'outer')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 7
    
    def test_smart_join_auto_detect(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.smart_join(df1, df2, None, 'inner')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    
    def test_smart_join_multiple_columns(self):
        df1 = pd.DataFrame({
            'id': [1, 2, 3],
            'code': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        
        df2 = pd.DataFrame({
            'id': [1, 2, 4],
            'code': ['A', 'B', 'D'],
            'amount': [100, 200, 300]
        })
        
        result = self.service.smart_join(df1, df2, ['id', 'code'], 'inner')
        
        assert len(result) == 2
    
    def test_smart_join_column_not_in_df1(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        with pytest.raises(ValueError, match="not found in first dataset"):
            self.service.smart_join(df1, df2, ['nonexistent'], 'inner')
    
    def test_smart_join_column_not_in_df2(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        df2 = df2.rename(columns={'id': 'identifier'})
        
        with pytest.raises(ValueError, match="not found in second dataset"):
            self.service.smart_join(df1, df2, ['id'], 'inner')
    
    def test_smart_join_no_common_columns(self):
        df1 = pd.DataFrame({'a': [1, 2, 3]})
        df2 = pd.DataFrame({'b': [4, 5, 6]})
        
        with pytest.raises(ValueError, match="Could not auto-detect join columns"):
            self.service.smart_join(df1, df2, None, 'inner')
    
    def test_detect_join_columns_with_id(self):
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'value': [10, 20]})
        df2 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'amount': [100, 200]})
        
        columns = self.service._detect_join_columns(df1, df2)
        
        assert 'id' in columns
        assert len(columns) == 1
    
    def test_detect_join_columns_with_key(self):
        df1 = pd.DataFrame({'user_key': [1, 2], 'value': [10, 20]})
        df2 = pd.DataFrame({'user_key': [1, 2], 'amount': [100, 200]})
        
        columns = self.service._detect_join_columns(df1, df2)
        
        assert 'user_key' in columns
    
    def test_detect_join_columns_no_common(self):
        df1 = pd.DataFrame({'a': [1, 2]})
        df2 = pd.DataFrame({'b': [3, 4]})
        
        columns = self.service._detect_join_columns(df1, df2)
        
        assert columns == []
    
    def test_detect_join_columns_priority(self):
        df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'value': [10, 20]})
        df2 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B'], 'amount': [100, 200]})
        
        columns = self.service._detect_join_columns(df1, df2)
        
        assert columns[0] == 'id'
    
    def test_multi_join_two_dataframes(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        result = self.service.multi_join([df1, df2], ['id'], 'inner')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
    
    def test_multi_join_three_dataframes(self):
        df1 = pd.DataFrame({'id': [1, 2, 3], 'value_a': [10, 20, 30]})
        df2 = pd.DataFrame({'id': [1, 2, 3], 'value_b': [100, 200, 300]})
        df3 = pd.DataFrame({'id': [1, 2, 3], 'value_c': [1000, 2000, 3000]})
        
        result = self.service.multi_join([df1, df2, df3], ['id'], 'inner')
        
        assert len(result) == 3
        assert 'value_a' in result.columns
        assert 'value_b' in result.columns
        assert 'value_c' in result.columns
    
    def test_multi_join_insufficient_dataframes(self):
        df1 = pd.DataFrame({'id': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="at least 2 DataFrames"):
            self.service.multi_join([df1], ['id'], 'inner')
    
    def test_concatenate_dataframes_vertical(self):
        df1 = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df2 = pd.DataFrame({'a': [5, 6], 'b': [7, 8]})
        
        result = self.service.concatenate_dataframes([df1, df2], axis=0)
        
        assert len(result) == 4
        assert list(result.columns) == ['a', 'b']
    
    def test_concatenate_dataframes_horizontal(self):
        df1 = pd.DataFrame({'a': [1, 2]})
        df2 = pd.DataFrame({'b': [3, 4]})
        
        result = self.service.concatenate_dataframes([df1, df2], axis=1)
        
        assert len(result.columns) == 2
        assert 'a' in result.columns
        assert 'b' in result.columns
    
    def test_concatenate_dataframes_ignore_index(self):
        df1 = pd.DataFrame({'a': [1, 2]}, index=[5, 6])
        df2 = pd.DataFrame({'a': [3, 4]}, index=[7, 8])
        
        result = self.service.concatenate_dataframes([df1, df2], axis=0, ignore_index=True)
        
        assert list(result.index) == [0, 1, 2, 3]
    
    def test_analyze_join_potential(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        analysis = self.service.analyze_join_potential(df1, df2)
        
        assert 'common_columns' in analysis
        assert 'recommended_join_columns' in analysis
        assert 'df1_shape' in analysis
        assert 'df2_shape' in analysis
        assert 'df1_columns' in analysis
        assert 'df2_columns' in analysis
    
    def test_analyze_join_potential_with_uniqueness(self, sample_join_dataframes):
        df1, df2 = sample_join_dataframes
        
        analysis = self.service.analyze_join_potential(df1, df2)
        
        assert 'column_uniqueness' in analysis
        assert 'id' in analysis['column_uniqueness']
        assert 'df1_unique_ratio' in analysis['column_uniqueness']['id']
        assert 'df2_unique_ratio' in analysis['column_uniqueness']['id']
    
    def test_analyze_join_potential_no_common(self):
        df1 = pd.DataFrame({'a': [1, 2]})
        df2 = pd.DataFrame({'b': [3, 4]})
        
        analysis = self.service.analyze_join_potential(df1, df2)
        
        assert analysis['common_columns'] == []
        assert analysis['recommended_join_columns'] == []
    
    def test_load_multiple_files(self, sample_join_files):
        file1, file2 = sample_join_files
        
        loaded_data = self.service.load_multiple_files([file1, file2])
        
        assert len(loaded_data) == 2
        assert file1 in loaded_data
        assert file2 in loaded_data
        
        df1, metadata1 = loaded_data[file1]
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(metadata1, dict)
    
    def test_load_multiple_files_with_sheets(self, sample_excel_file):
        loaded_data = self.service.load_multiple_files([sample_excel_file], ['TestSheet'])
        
        assert len(loaded_data) == 1
        df, metadata = loaded_data[sample_excel_file]
        assert metadata['sheet_name'] == 'TestSheet'
    
    def test_load_multiple_files_nonexistent(self):
        with pytest.raises(ValueError, match="Error loading"):
            self.service.load_multiple_files(['nonexistent.xlsx'])