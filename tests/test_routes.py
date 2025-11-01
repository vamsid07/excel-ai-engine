import pytest
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path
import pandas as pd


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    
    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'services' in data
        assert 'version' in data


class TestGenerateSampleData:
    
    def test_generate_sample_data_default(self, client):
        response = client.post("/api/v1/generate-sample-data")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'filepath' in data
        assert data['rows_generated'] == 1000
    
    def test_generate_sample_data_custom_rows(self, client):
        response = client.post("/api/v1/generate-sample-data?rows=500")
        
        assert response.status_code == 200
        data = response.json()
        assert data['rows_generated'] == 500
    
    def test_generate_sample_data_no_unstructured(self, client):
        response = client.post("/api/v1/generate-sample-data?rows=100&include_unstructured=false")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['sheets']) == 1
    
    def test_generate_sample_data_invalid_rows(self, client):
        response = client.post("/api/v1/generate-sample-data?rows=0")
        
        assert response.status_code == 400
    
    def test_generate_sample_data_too_many_rows(self, client):
        response = client.post("/api/v1/generate-sample-data?rows=200000")
        
        assert response.status_code == 400


class TestUploadEndpoint:
    
    def test_upload_excel_success(self, client, sample_excel_file):
        with open(sample_excel_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'filepath' in data
        assert 'sheets' in data
    
    def test_upload_invalid_format(self, client, test_data_dir):
        test_file = test_data_dir / "test.txt"
        test_file.write_text("test content")
        
        with open(test_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        assert response.status_code == 400
    
    def test_upload_empty_file(self, client, test_data_dir):
        test_file = test_data_dir / "empty.xlsx"
        test_file.touch()
        
        with open(test_file, 'rb') as f:
            response = client.post(
                "/api/v1/upload",
                files={"file": ("empty.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        
        assert response.status_code == 400


class TestQueryEndpoint:
    
    def test_query_success(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_excel_file,
                "query": "Calculate average salary",
                "sheet_name": "TestSheet"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'result' in data
        assert 'generated_code' in data
    
    def test_query_missing_filepath(self, client):
        response = client.post(
            "/api/v1/query",
            data={
                "query": "Calculate average salary"
            }
        )
        
        assert response.status_code == 422
    
    def test_query_missing_query(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_excel_file
            }
        )
        
        assert response.status_code == 422
    
    def test_query_empty_filepath(self, client):
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": "",
                "query": "test"
            }
        )
        
        assert response.status_code == 400
    
    def test_query_empty_query(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": sample_excel_file,
                "query": ""
            }
        )
        
        assert response.status_code == 400
    
    def test_query_nonexistent_file(self, client):
        response = client.post(
            "/api/v1/query",
            data={
                "filepath": "nonexistent.xlsx",
                "query": "Calculate average"
            }
        )
        
        assert response.status_code == 404


class TestJoinEndpoint:
    
    def test_join_files(self, client, sample_join_files):
        file1, file2 = sample_join_files
        
        response = client.post(
            "/api/v1/join",
            data={
                "file1": file1,
                "file2": file2,
                "how": "inner"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'result' in data
    
    def test_join_with_columns(self, client, sample_join_files):
        file1, file2 = sample_join_files
        
        response = client.post(
            "/api/v1/join",
            data={
                "file1": file1,
                "file2": file2,
                "join_columns": "id",
                "how": "left"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['join_type'] == 'left'
    
    def test_join_invalid_type(self, client, sample_join_files):
        file1, file2 = sample_join_files
        
        response = client.post(
            "/api/v1/join",
            data={
                "file1": file1,
                "file2": file2,
                "how": "invalid"
            }
        )
        
        assert response.status_code == 400
    
    def test_join_nonexistent_file1(self, client, sample_join_files):
        file1, file2 = sample_join_files
        
        response = client.post(
            "/api/v1/join",
            data={
                "file1": "nonexistent.xlsx",
                "file2": file2,
                "how": "inner"
            }
        )
        
        assert response.status_code == 404


class TestExportEndpoint:
    
    def test_export_result(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/export",
            data={
                "filepath": sample_excel_file,
                "query": "Show all data",
                "sheet_name": "TestSheet"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'output_file' in data
    
    def test_export_with_formatting(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/export",
            data={
                "filepath": sample_excel_file,
                "query": "Show all data",
                "sheet_name": "TestSheet",
                "formatted": "true"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'output_file' in data
    
    def test_export_custom_filename(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/export",
            data={
                "filepath": sample_excel_file,
                "query": "Show all data",
                "sheet_name": "TestSheet",
                "output_filename": "my_export.xlsx"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'my_export.xlsx' in data['output_file']


class TestAnalyzeTextEndpoint:
    
    def test_analyze_text_sentiment(self, client, sample_text_excel):
        response = client.post(
            "/api/v1/analyze-text",
            data={
                "filepath": sample_text_excel,
                "column": "customer_feedback",
                "analysis_type": "sentiment",
                "sheet_name": "TextData"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'result' in data
    
    def test_analyze_text_invalid_type(self, client, sample_text_excel):
        response = client.post(
            "/api/v1/analyze-text",
            data={
                "filepath": sample_text_excel,
                "column": "customer_feedback",
                "analysis_type": "invalid",
                "sheet_name": "TextData"
            }
        )
        
        assert response.status_code == 400
    
    def test_analyze_text_invalid_column(self, client, sample_text_excel):
        response = client.post(
            "/api/v1/analyze-text",
            data={
                "filepath": sample_text_excel,
                "column": "nonexistent",
                "analysis_type": "sentiment",
                "sheet_name": "TextData"
            }
        )
        
        assert response.status_code == 400


class TestDownloadEndpoint:
    
    def test_download_file(self, client, test_data_dir):
        test_file = test_data_dir / "download_test.xlsx"
        df = pd.DataFrame({'a': [1, 2, 3]})
        df.to_excel(test_file, index=False)
        
        Path("data/output").mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(test_file, "data/output/download_test.xlsx")
        
        response = client.get("/api/v1/download/download_test.xlsx")
        
        assert response.status_code == 200
    
    def test_download_nonexistent_file(self, client):
        response = client.get("/api/v1/download/nonexistent.xlsx")
        
        assert response.status_code == 404


class TestAnalyzeEndpoint:
    
    def test_analyze_excel(self, client, sample_excel_file):
        response = client.post(
            "/api/v1/analyze",
            data={
                "filepath": sample_excel_file,
                "sheet_name": "TestSheet"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'analysis' in data
        assert 'shape' in data['analysis']
        assert 'columns' in data['analysis']
    
    def test_analyze_nonexistent_file(self, client):
        response = client.post(
            "/api/v1/analyze",
            data={
                "filepath": "nonexistent.xlsx"
            }
        )
        
        assert response.status_code == 404


class TestSheetsEndpoint:
    
    def test_list_sheets(self, client, sample_excel_file):
        response = client.get(f"/api/v1/sheets/{sample_excel_file}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'sheets' in data
        assert len(data['sheets']) > 0
    
    def test_list_sheets_nonexistent_file(self, client):
        response = client.get("/api/v1/sheets/nonexistent.xlsx")
        
        assert response.status_code == 404


class TestHistoryEndpoints:
    
    def test_get_history(self, client):
        response = client.get("/api/v1/history")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'history' in data
    
    def test_get_history_with_limit(self, client):
        response = client.get("/api/v1/history?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data['history']) <= 5
    
    def test_get_history_invalid_limit(self, client):
        response = client.get("/api/v1/history?limit=2000")
        
        assert response.status_code == 400
    
    def test_get_history_stats(self, client):
        response = client.get("/api/v1/history/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'statistics' in data


class TestRootEndpoint:
    
    def test_root(self, client):
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
        assert 'features' in data