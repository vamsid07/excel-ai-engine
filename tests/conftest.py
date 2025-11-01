import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, timedelta


@pytest.fixture(scope="session")
def test_data_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_dataframe():
    np.random.seed(42)
    data = {
        'id': range(1, 101),
        'name': [f'Person_{i}' for i in range(1, 101)],
        'age': np.random.randint(20, 70, 100),
        'salary': np.random.randint(30000, 150000, 100),
        'department': np.random.choice(['Sales', 'Engineering', 'HR', 'Marketing'], 100),
        'join_date': [datetime.now() - timedelta(days=np.random.randint(365, 3650)) for _ in range(100)],
        'performance_score': np.random.uniform(1.0, 5.0, 100).round(2),
        'projects_completed': np.random.randint(0, 30, 100),
        'city': np.random.choice(['New York', 'San Francisco', 'Chicago', 'Boston'], 100)
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_excel_file(sample_dataframe, test_data_dir):
    filepath = test_data_dir / "test_data.xlsx"
    sample_dataframe.to_excel(filepath, index=False, sheet_name='TestSheet')
    return str(filepath)


@pytest.fixture
def sample_text_dataframe():
    data = {
        'id': range(1, 51),
        'customer_feedback': [
            'Great service! Very satisfied.' if i % 3 == 0
            else 'Poor experience. Disappointed.' if i % 3 == 1
            else 'Average product. Nothing special.'
            for i in range(1, 51)
        ],
        'product_review': [f'Review text {i} with quality and excellent features' for i in range(1, 51)],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_text_excel(sample_text_dataframe, test_data_dir):
    filepath = test_data_dir / "test_text.xlsx"
    sample_text_dataframe.to_excel(filepath, index=False, sheet_name='TextData')
    return str(filepath)


@pytest.fixture
def sample_join_dataframes():
    df1 = pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'value_a': [10, 20, 30, 40, 50]
    })
    
    df2 = pd.DataFrame({
        'id': [1, 2, 3, 6, 7],
        'name': ['Alice', 'Bob', 'Charlie', 'Frank', 'Grace'],
        'value_b': [100, 200, 300, 400, 500]
    })
    
    return df1, df2


@pytest.fixture
def sample_join_files(sample_join_dataframes, test_data_dir):
    df1, df2 = sample_join_dataframes
    
    file1 = test_data_dir / "join_file1.xlsx"
    file2 = test_data_dir / "join_file2.xlsx"
    
    df1.to_excel(file1, index=False)
    df2.to_excel(file2, index=False)
    
    return str(file1), str(file2)


@pytest.fixture
def mock_llm_response():
    return {
        "code": "result = df.groupby('department')['salary'].mean().reset_index()",
        "explanation": "Calculate average salary by department",
        "operation_type": "aggregation",
        "creates_new_column": False,
        "new_column_name": None
    }


@pytest.fixture
def sample_pivot_dataframe():
    data = {
        'department': ['Sales', 'Sales', 'Engineering', 'Engineering', 'HR', 'HR'],
        'city': ['New York', 'Chicago', 'New York', 'Chicago', 'New York', 'Chicago'],
        'salary': [60000, 65000, 80000, 85000, 50000, 55000]
    }
    return pd.DataFrame(data)