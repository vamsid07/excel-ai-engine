import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from app.services.llm_service import LLMService
import requests


class TestLLMService:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = LLMService()
    
    def test_init(self):
        assert self.service.ollama_url is not None
        assert self.service.model is not None
    
    def test_validate_columns_in_query_valid(self):
        query = "Calculate average salary by department"
        columns = ['id', 'name', 'salary', 'department', 'age']
        
        result = self.service.validate_columns_in_query(query, columns)
        
        assert result['valid'] is True
        assert 'salary' in result['mentioned_columns']
        assert 'department' in result['mentioned_columns']
    
    def test_validate_columns_in_query_missing(self):
        query = "Calculate average nonexistent_column by department"
        columns = ['id', 'name', 'salary', 'department']
        
        result = self.service.validate_columns_in_query(query, columns)
        
        assert 'nonexistent_column' in result['potential_missing']
    
    def test_validate_columns_fuzzy_match(self):
        query = "Show total compensation"
        columns = ['id', 'total_compensation', 'salary']
        
        result = self.service.validate_columns_in_query(query, columns)
        
        assert 'total_compensation' in result['mentioned_columns']
    
    @patch('requests.post')
    def test_generate_pandas_code_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': '{"code": "result = df.mean()", "explanation": "Calculate mean", "operation_type": "aggregation", "creates_new_column": false, "new_column_name": null}'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        df_info = {
            'columns': ['salary', 'age'],
            'dtypes': ['int64', 'int64'],
            'shape': (100, 2),
            'sample_data': 'sample',
            'null_counts': {}
        }
        
        result = self.service.generate_pandas_code("Calculate mean", df_info)
        
        assert result['success'] is True
        assert 'code' in result
        assert result['operation_type'] == 'aggregation'
    
    @patch('requests.post')
    def test_generate_pandas_code_json_error(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            'message': {
                'content': 'invalid json'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        df_info = {
            'columns': ['salary'],
            'dtypes': ['int64'],
            'shape': (100, 1),
            'sample_data': 'sample',
            'null_counts': {}
        }
        
        result = self.service.generate_pandas_code("test query", df_info)
        
        assert result['success'] is False
        assert 'Failed to parse response' in result['error']
    
    @patch('requests.post')
    def test_generate_pandas_code_connection_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        df_info = {
            'columns': ['salary'],
            'dtypes': ['int64'],
            'shape': (100, 1),
            'sample_data': 'sample',
            'null_counts': {}
        }
        
        result = self.service.generate_pandas_code("test query", df_info)
        
        assert result['success'] is False
        assert 'Cannot connect to Ollama' in result['error']
    
    @patch('requests.post')
    def test_generate_pandas_code_timeout(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()
        
        df_info = {
            'columns': ['salary'],
            'dtypes': ['int64'],
            'shape': (100, 1),
            'sample_data': 'sample',
            'null_counts': {}
        }
        
        result = self.service.generate_pandas_code("test query", df_info)
        
        assert result['success'] is False
        assert 'timed out' in result['error']
    
    def test_validate_and_enhance_code_valid(self):
        code = "result = df['salary'].mean()"
        
        validated = self.service.validate_and_enhance_code(code)
        
        assert validated == code
    
    def test_validate_and_enhance_code_forbidden_eval(self):
        code = "result = eval('df.mean()')"
        
        with pytest.raises(ValueError, match="Forbidden operation"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_forbidden_open(self):
        code = "result = open('file.txt')"
        
        with pytest.raises(ValueError, match="Forbidden operation"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_forbidden_os(self):
        code = "import os\nresult = os.listdir()"
        
        with pytest.raises(ValueError, match="Forbidden operation"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_forbidden_subprocess(self):
        code = "import subprocess\nresult = df.mean()"
        
        with pytest.raises(ValueError, match="Forbidden operation"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_unauthorized_import(self):
        code = "import requests\nresult = df.mean()"
        
        with pytest.raises(ValueError, match="Unauthorized import"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_no_result(self):
        code = "x = df['salary'].mean()"
        
        with pytest.raises(ValueError, match="must assign to 'result'"):
            self.service.validate_and_enhance_code(code)
    
    def test_validate_and_enhance_code_allowed_pandas(self):
        code = "import pandas as pd\nresult = df.mean()"
        
        validated = self.service.validate_and_enhance_code(code)
        
        assert validated == code
    
    def test_validate_and_enhance_code_allowed_numpy(self):
        code = "import numpy as np\nresult = df.mean()"
        
        validated = self.service.validate_and_enhance_code(code)
        
        assert validated == code
    
    def test_validate_and_enhance_code_allowed_datetime(self):
        code = "from datetime import datetime\nresult = df.mean()"
        
        validated = self.service.validate_and_enhance_code(code)
        
        assert validated == code
    
    def test_analyze_unstructured_text_sentiment_positive(self):
        text_data = pd.Series(['Great product! Love it!', 'Excellent service'])
        
        result = self.service.analyze_unstructured_text(text_data, 'sentiment')
        
        assert result[0] == 'positive'
        assert result[1] == 'positive'
    
    def test_analyze_unstructured_text_sentiment_negative(self):
        text_data = pd.Series(['Terrible experience', 'Worst product ever'])
        
        result = self.service.analyze_unstructured_text(text_data, 'sentiment')
        
        assert result[0] == 'negative'
        assert result[1] == 'negative'
    
    def test_analyze_unstructured_text_sentiment_neutral(self):
        text_data = pd.Series(['The product arrived', 'Nothing special'])
        
        result = self.service.analyze_unstructured_text(text_data, 'sentiment')
        
        assert result[0] == 'neutral'
        assert result[1] == 'neutral'
    
    def test_analyze_unstructured_text_length(self):
        text_data = pd.Series(['Short', 'Much longer text here'])
        
        result = self.service.analyze_unstructured_text(text_data, 'length')
        
        assert result[0] == 5
        assert result[1] == 21
    
    def test_build_system_prompt(self):
        prompt = self.service._build_system_prompt()
        
        assert 'pandas' in prompt
        assert 'result' in prompt
        assert 'DataFrame' in prompt
    
    def test_build_user_prompt(self):
        df_info = {
            'columns': ['salary', 'department'],
            'dtypes': ['int64', 'object'],
            'shape': (100, 2),
            'sample_data': 'test data',
            'null_counts': {'salary': 0, 'department': 0}
        }
        
        prompt = self.service._build_user_prompt('Calculate average', df_info, 'df')
        
        assert 'Calculate average' in prompt
        assert 'salary' in prompt
        assert 'department' in prompt
        assert 'df' in prompt