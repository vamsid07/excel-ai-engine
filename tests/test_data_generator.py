import pytest
import pandas as pd
from pathlib import Path
from app.utils.data_generator import DataGenerator


class TestDataGenerator:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.generator = DataGenerator(seed=42)
    
    def test_init(self):
        assert self.generator.fake is not None
    
    def test_init_with_seed(self):
        gen1 = DataGenerator(seed=42)
        gen2 = DataGenerator(seed=42)
        
        df1 = gen1.generate_structured_data(rows=10)
        df2 = gen2.generate_structured_data(rows=10)
        
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_generate_structured_data_default(self):
        df = self.generator.generate_structured_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1000
        assert len(df.columns) == 10
    
    def test_generate_structured_data_custom_rows(self):
        df = self.generator.generate_structured_data(rows=500)
        
        assert len(df) == 500
    
    def test_generate_structured_data_columns(self):
        df = self.generator.generate_structured_data()
        
        expected_columns = [
            'id', 'name', 'email', 'age', 'salary', 
            'department', 'join_date', 'performance_score', 
            'projects_completed', 'city'
        ]
        
        assert list(df.columns) == expected_columns
    
    def test_generate_structured_data_id_sequential(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert list(df['id']) == list(range(1, 101))
    
    def test_generate_structured_data_age_range(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df['age'].min() >= 18
        assert df['age'].max() < 80
    
    def test_generate_structured_data_salary_range(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df['salary'].min() >= 30000
        assert df['salary'].max() < 200000
    
    def test_generate_structured_data_departments(self):
        df = self.generator.generate_structured_data(rows=100)
        
        departments = ['Sales', 'Engineering', 'HR', 'Marketing', 'Finance']
        assert all(dept in departments for dept in df['department'].unique())
    
    def test_generate_structured_data_join_date_type(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert pd.api.types.is_datetime64_any_dtype(df['join_date'])
    
    def test_generate_structured_data_performance_score_range(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df['performance_score'].min() >= 1.0
        assert df['performance_score'].max() <= 5.0
    
    def test_generate_structured_data_projects_range(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df['projects_completed'].min() >= 0
        assert df['projects_completed'].max() < 50
    
    def test_generate_unstructured_data_default(self):
        df = self.generator.generate_unstructured_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1000
        assert len(df.columns) == 5
    
    def test_generate_unstructured_data_custom_rows(self):
        df = self.generator.generate_unstructured_data(rows=250)
        
        assert len(df) == 250
    
    def test_generate_unstructured_data_columns(self):
        df = self.generator.generate_unstructured_data()
        
        expected_columns = [
            'id', 'customer_feedback', 'product_review', 
            'support_ticket', 'notes'
        ]
        
        assert list(df.columns) == expected_columns
    
    def test_generate_unstructured_data_id_sequential(self):
        df = self.generator.generate_unstructured_data(rows=50)
        
        assert list(df['id']) == list(range(1, 51))
    
    def test_generate_unstructured_data_has_text(self):
        df = self.generator.generate_unstructured_data(rows=10)
        
        assert all(len(str(text)) > 0 for text in df['customer_feedback'])
        assert all(len(str(text)) > 0 for text in df['product_review'])
        assert all(len(str(text)) > 0 for text in df['support_ticket'])
        assert all(len(str(text)) > 0 for text in df['notes'])
    
    def test_generate_feedback_variety(self):
        feedbacks = [self.generator._generate_feedback() for _ in range(20)]
        
        unique_feedbacks = set(feedbacks)
        assert len(unique_feedbacks) > 1
    
    def test_generate_review_variety(self):
        reviews = [self.generator._generate_review() for _ in range(20)]
        
        unique_reviews = set(reviews)
        assert len(unique_reviews) > 1
    
    def test_generate_ticket_variety(self):
        tickets = [self.generator._generate_ticket() for _ in range(20)]
        
        unique_tickets = set(tickets)
        assert len(unique_tickets) > 1
    
    def test_save_to_excel_structured_only(self, test_data_dir):
        structured_df = self.generator.generate_structured_data(rows=50)
        filepath = test_data_dir / "test_structured.xlsx"
        
        result_path = self.generator.save_to_excel(structured_df, None, str(filepath))
        
        assert Path(result_path).exists()
        
        xl_file = pd.ExcelFile(result_path)
        assert 'Structured_Data' in xl_file.sheet_names
        assert 'Unstructured_Data' not in xl_file.sheet_names
    
    def test_save_to_excel_both_sheets(self, test_data_dir):
        structured_df = self.generator.generate_structured_data(rows=50)
        unstructured_df = self.generator.generate_unstructured_data(rows=50)
        filepath = test_data_dir / "test_both.xlsx"
        
        result_path = self.generator.save_to_excel(
            structured_df, 
            unstructured_df, 
            str(filepath)
        )
        
        assert Path(result_path).exists()
        
        xl_file = pd.ExcelFile(result_path)
        assert 'Structured_Data' in xl_file.sheet_names
        assert 'Unstructured_Data' in xl_file.sheet_names
    
    def test_save_to_excel_creates_directory(self, test_data_dir):
        structured_df = self.generator.generate_structured_data(rows=10)
        filepath = test_data_dir / "subdir" / "test.xlsx"
        
        result_path = self.generator.save_to_excel(structured_df, None, str(filepath))
        
        assert Path(result_path).exists()
    
    def test_save_to_excel_data_integrity(self, test_data_dir):
        structured_df = self.generator.generate_structured_data(rows=50)
        filepath = test_data_dir / "integrity_test.xlsx"
        
        result_path = self.generator.save_to_excel(structured_df, None, str(filepath))
        
        loaded_df = pd.read_excel(result_path, sheet_name='Structured_Data')
        
        assert len(loaded_df) == len(structured_df)
        assert list(loaded_df.columns) == list(structured_df.columns)
    
    def test_generate_structured_data_no_nulls(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df.isnull().sum().sum() == 0
    
    def test_generate_unstructured_data_no_nulls(self):
        df = self.generator.generate_unstructured_data(rows=100)
        
        assert df.isnull().sum().sum() == 0
    
    def test_generate_structured_data_unique_emails(self):
        df = self.generator.generate_structured_data(rows=100)
        
        assert df['email'].nunique() == len(df)
    
    def test_generate_structured_data_dtypes(self):
        df = self.generator.generate_structured_data(rows=10)
        
        assert df['id'].dtype == 'int64'
        assert df['name'].dtype == 'object'
        assert df['email'].dtype == 'object'
        assert df['age'].dtype in ['int32', 'int64']
        assert df['salary'].dtype in ['int32', 'int64']
        assert df['department'].dtype == 'object'
        assert pd.api.types.is_datetime64_any_dtype(df['join_date'])
        assert df['performance_score'].dtype == 'float64'
        assert df['projects_completed'].dtype in ['int32', 'int64']
        assert df['city'].dtype == 'object'
    
    def test_generate_small_dataset(self):
        df = self.generator.generate_structured_data(rows=1)
        
        assert len(df) == 1
        assert df['id'].iloc[0] == 1
    
    def test_generate_large_dataset(self):
        df = self.generator.generate_structured_data(rows=5000)
        
        assert len(df) == 5000
        assert df['id'].iloc[-1] == 5000
    
    def test_feedback_sentiments_distributed(self):
        df = self.generator.generate_unstructured_data(rows=100)
        
        feedbacks = df['customer_feedback'].unique()
        assert len(feedbacks) > 5
    
    def test_reproducibility_with_same_seed(self):
        gen1 = DataGenerator(seed=123)
        gen2 = DataGenerator(seed=123)
        
        df1 = gen1.generate_structured_data(rows=50)
        df2 = gen2.generate_structured_data(rows=50)
        
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_different_seeds_produce_different_data(self):
        gen1 = DataGenerator(seed=123)
        gen2 = DataGenerator(seed=456)
        
        df1 = gen1.generate_structured_data(rows=50)
        df2 = gen2.generate_structured_data(rows=50)
        
        assert not df1['salary'].equals(df2['salary'])