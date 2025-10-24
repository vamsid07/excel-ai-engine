"""
Unit tests for Excel AI Engine API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from pathlib import Path

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns health status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_health_check(self):
        """Test API v1 health endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data


class TestDataGeneration:
    """Test data generation endpoints"""
    
    def test_generate_sample_data_default(self):
        """Test generating sample data with default parameters"""
        response = client.post("/api/v1/generate-sample-data")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["rows_generated"] == 1000
        assert "Structured_Data" in data["sheets"]
    
    def test_generate_sample_data_custom_rows(self):
        """Test generating sample data with custom row count"""
        response = client.post("/api/v1/generate-sample-data?rows=500&include_unstructured=false")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["rows_generated"] == 500
        assert "Unstructured_Data" not in data["sheets"]
    
    def test_generated_file_exists(self):
        """Test that generated file actually exists"""
        response = client.post("/api/v1/generate-sample-data?rows=100")
        assert response.status_code == 200
        data = response.json()
        filepath = data["filepath"]
        assert os.path.exists(filepath)


class TestFileOperations:
    """Test file upload and listing operations"""
    
    @pytest.fixture
    def sample_excel_file(self):
        """Create a sample Excel file for testing"""
        # First generate the file
        response = client.post("/api/v1/generate-sample-data?rows=100")
        assert response.status_code == 200
        return "data/output/sample_data.xlsx"
    
    def test_list_operations(self):
        """Test listing supported operations"""
        response = client.get("/api/v1/operations")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "supported_operations" in data
        assert len(data["supported_operations"]) > 0
    
    def test_upload_invalid_file_type(self):
        """Test uploading non-Excel file"""
        files = {"file": ("test.txt", b"not an excel file", "text/plain")}
        response = client.post("/api/v1/upload", files=files)
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]
    
    def test_list_sheets(self, sample_excel_file):
        """Test listing sheets in Excel file"""
        response = client.get(f"/api/v1/sheets/{sample_excel_file}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "sheets" in data
        assert len(data["sheets"]) > 0
    
    def test_analyze_excel(self, sample_excel_file):
        """Test analyzing Excel file"""
        response = client.post(
            "/api/v1/analyze",
            data={"filepath": sample_excel_file}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "analysis" in data
        assert "shape" in data["analysis"]
        assert "columns" in data["analysis"]


class TestQueryExecution:
    """Test natural language query execution"""
    
    @pytest.fixture
    def sample_file_with_data(self):
        """Generate sample data file"""
        response = client.post("/api/v1/generate-sample-data?rows=100")
        return "data/output/sample_data.xlsx"
    
    def test_query_simple_aggregation(self, sample_file_with_data):
        """Test simple aggregation query"""
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_file_with_data,
                "query": "Calculate average salary",
                "sheet_name": "Structured_Data"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "result" in data
        assert "generated_code" in data
    
    def test_query_filtering(self, sample_file_with_data):
        """Test filtering query"""
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_file_with_data,
                "query": "Show employees with salary greater than 50000",
                "sheet_name": "Structured_Data"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["operation_type"] in ["filter", "filtering"]
    
    def test_query_groupby(self, sample_file_with_data):
        """Test groupby aggregation query"""
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_file_with_data,
                "query": "Calculate average salary by department",
                "sheet_name": "Structured_Data"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["operation_type"] == "aggregation"
    
    def test_query_nonexistent_file(self):
        """Test query with non-existent file"""
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": "data/input/nonexistent.xlsx",
                "query": "Show all data"
            }
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_query_math_operation(self, sample_file_with_data):
        """Test mathematical operation query"""
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_file_with_data,
                "query": "Add a column for salary doubled",
                "sheet_name": "Structured_Data"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestExcelService:
    """Test Excel service functions directly"""
    
    def test_dataframe_info_extraction(self):
        """Test DataFrame info extraction"""
        from app.services.excel_service import ExcelService
        import pandas as pd
        
        service = ExcelService()
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': ['x', 'y', 'z']
        })
        
        info = service._extract_dataframe_info(df)
        assert info['shape'] == (3, 2)
        assert info['columns'] == ['A', 'B']
        assert len(info['dtypes']) == 2


class TestLLMService:
    """Test LLM service functions"""
    
    def test_code_validation_forbids_dangerous_operations(self):
        """Test that code validation blocks dangerous operations"""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        dangerous_codes = [
            "import os\nos.system('rm -rf /')",
            "eval('malicious code')",
            "exec('bad stuff')",
            "__import__('subprocess')",
            "open('/etc/passwd', 'r')"
        ]
        
        for code in dangerous_codes:
            with pytest.raises(ValueError):
                service.validate_and_enhance_code(code)
    
    def test_code_validation_allows_safe_operations(self):
        """Test that code validation allows safe pandas operations"""
        from app.services.llm_service import LLMService
        
        service = LLMService()
        
        safe_codes = [
            "result = df.mean()",
            "result = df[df['salary'] > 50000]",
            "result = df.groupby('department')['salary'].mean()",
            "import pandas as pd\nresult = df.head()"
        ]
        
        for code in safe_codes:
            validated = service.validate_and_enhance_code(code)
            assert validated == code


# Run tests with: pytest app/tests/test_api.py -v
# Run with coverage: pytest app/tests/test_api.py --cov=app --cov-report=html