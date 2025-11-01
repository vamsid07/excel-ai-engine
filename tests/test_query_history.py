import pytest
import json
from pathlib import Path
from app.services.query_history import QueryHistory


class TestQueryHistory:
    
    @pytest.fixture(autouse=True)
    def setup(self, test_data_dir):
        self.history_file = test_data_dir / "test_history.json"
        self.service = QueryHistory()
        self.service.history_file = self.history_file
        self.service.history = []
    
    def test_init(self):
        assert self.service.history_file is not None
        assert isinstance(self.service.history, list)
    
    def test_add_query_success(self):
        query_id = self.service.add_query(
            query="Calculate average salary",
            filepath="test.xlsx",
            result_type="dataframe",
            success=True,
            execution_time=1.5,
            generated_code="result = df.mean()",
            result_shape=(10, 5)
        )
        
        assert query_id is not None
        assert len(self.service.history) == 1
        assert self.service.history[0]['query'] == "Calculate average salary"
        assert self.service.history[0]['success'] is True
    
    def test_add_query_failure(self):
        query_id = self.service.add_query(
            query="Invalid query",
            filepath="test.xlsx",
            result_type="error",
            success=False,
            execution_time=0.5,
            error="Query failed"
        )
        
        assert query_id is not None
        assert len(self.service.history) == 1
        assert self.service.history[0]['success'] is False
        assert self.service.history[0]['error'] == "Query failed"
    
    def test_add_query_contains_timestamp(self):
        query_id = self.service.add_query(
            query="Test query",
            filepath="test.xlsx",
            result_type="dataframe",
            success=True,
            execution_time=1.0
        )
        
        assert 'timestamp' in self.service.history[0]
        assert isinstance(self.service.history[0]['timestamp'], str)
    
    def test_add_query_contains_id(self):
        query_id = self.service.add_query(
            query="Test query",
            filepath="test.xlsx",
            result_type="dataframe",
            success=True,
            execution_time=1.0
        )
        
        assert 'id' in self.service.history[0]
        assert self.service.history[0]['id'] == query_id
    
    def test_get_recent_queries_default_limit(self):
        for i in range(15):
            self.service.add_query(
                query=f"Query {i}",
                filepath="test.xlsx",
                result_type="dataframe",
                success=True,
                execution_time=1.0
            )
        
        recent = self.service.get_recent_queries()
        
        assert len(recent) == 10
    
    def test_get_recent_queries_custom_limit(self):
        for i in range(10):
            self.service.add_query(
                query=f"Query {i}",
                filepath="test.xlsx",
                result_type="dataframe",
                success=True,
                execution_time=1.0
            )
        
        recent = self.service.get_recent_queries(limit=5)
        
        assert len(recent) == 5
    
    def test_get_recent_queries_success_only(self):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Query 2", "test.xlsx", "error", False, 0.5, error="Failed")
        self.service.add_query("Query 3", "test.xlsx", "dataframe", True, 1.0)
        
        recent = self.service.get_recent_queries(success_only=True)
        
        assert len(recent) == 2
        assert all(q['success'] for q in recent)
    
    def test_get_recent_queries_sorted_by_timestamp(self):
        self.service.add_query("Old query", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("New query", "test.xlsx", "dataframe", True, 1.0)
        
        recent = self.service.get_recent_queries()
        
        assert recent[0]['query'] == "New query"
        assert recent[1]['query'] == "Old query"
    
    def test_get_query_by_id_found(self):
        query_id = self.service.add_query(
            query="Find me",
            filepath="test.xlsx",
            result_type="dataframe",
            success=True,
            execution_time=1.0
        )
        
        found = self.service.get_query_by_id(query_id)
        
        assert found is not None
        assert found['query'] == "Find me"
        assert found['id'] == query_id
    
    def test_get_query_by_id_not_found(self):
        found = self.service.get_query_by_id("nonexistent-id")
        
        assert found is None
    
    def test_search_queries_found(self):
        self.service.add_query("Calculate average salary", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Filter by department", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Calculate total salary", "test.xlsx", "dataframe", True, 1.0)
        
        results = self.service.search_queries("salary")
        
        assert len(results) == 2
        assert all('salary' in r['query'].lower() for r in results)
    
    def test_search_queries_case_insensitive(self):
        self.service.add_query("Calculate AVERAGE", "test.xlsx", "dataframe", True, 1.0)
        
        results = self.service.search_queries("average")
        
        assert len(results) == 1
    
    def test_search_queries_with_limit(self):
        for i in range(25):
            self.service.add_query(f"Query test {i}", "test.xlsx", "dataframe", True, 1.0)
        
        results = self.service.search_queries("test", limit=10)
        
        assert len(results) == 10
    
    def test_search_queries_not_found(self):
        self.service.add_query("Some query", "test.xlsx", "dataframe", True, 1.0)
        
        results = self.service.search_queries("nonexistent")
        
        assert len(results) == 0
    
    def test_get_statistics_empty(self):
        stats = self.service.get_statistics()
        
        assert stats['total_queries'] == 0
        assert stats['successful_queries'] == 0
        assert stats['failed_queries'] == 0
        assert stats['success_rate'] == 0
        assert stats['avg_execution_time'] == 0
    
    def test_get_statistics_with_data(self):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Query 2", "test.xlsx", "error", False, 0.5)
        self.service.add_query("Query 3", "test.xlsx", "dataframe", True, 2.0)
        
        stats = self.service.get_statistics()
        
        assert stats['total_queries'] == 3
        assert stats['successful_queries'] == 2
        assert stats['failed_queries'] == 1
        assert stats['success_rate'] == pytest.approx(66.67, rel=0.01)
        assert stats['avg_execution_time_seconds'] == pytest.approx(1.5, rel=0.01)
    
    def test_get_statistics_top_queries(self):
        self.service.add_query("Popular query", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Popular query", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Rare query", "test.xlsx", "dataframe", True, 1.0)
        
        stats = self.service.get_statistics()
        
        assert 'top_queries' in stats
        assert len(stats['top_queries']) > 0
        assert stats['top_queries'][0]['query'] == "Popular query"
        assert stats['top_queries'][0]['count'] == 2
    
    def test_clear_history(self):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        self.service.add_query("Query 2", "test.xlsx", "dataframe", True, 1.0)
        
        self.service.clear_history()
        
        assert len(self.service.history) == 0
    
    def test_delete_query_found(self):
        query_id = self.service.add_query("Delete me", "test.xlsx", "dataframe", True, 1.0)
        
        result = self.service.delete_query(query_id)
        
        assert result is True
        assert len(self.service.history) == 0
    
    def test_delete_query_not_found(self):
        result = self.service.delete_query("nonexistent-id")
        
        assert result is False
    
    def test_delete_query_preserves_others(self):
        id1 = self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        id2 = self.service.add_query("Query 2", "test.xlsx", "dataframe", True, 1.0)
        
        self.service.delete_query(id1)
        
        assert len(self.service.history) == 1
        assert self.service.history[0]['id'] == id2
    
    def test_export_history_default_path(self):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        
        export_path = self.service.export_history()
        
        assert Path(export_path).exists()
        
        with open(export_path, 'r') as f:
            exported = json.load(f)
        
        assert len(exported) == 1
        assert exported[0]['query'] == "Query 1"
    
    def test_export_history_custom_path(self, test_data_dir):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        
        custom_path = test_data_dir / "custom_export.json"
        export_path = self.service.export_history(str(custom_path))
        
        assert export_path == str(custom_path)
        assert Path(export_path).exists()
    
    def test_save_and_load_history(self):
        self.service.add_query("Query 1", "test.xlsx", "dataframe", True, 1.0)
        self.service._save_history()
        
        new_service = QueryHistory()
        new_service.history_file = self.history_file
        new_service._load_history()
        
        assert len(new_service.history) == 1
        assert new_service.history[0]['query'] == "Query 1"
    
    def test_load_history_nonexistent_file(self, test_data_dir):
        new_service = QueryHistory()
        new_service.history_file = test_data_dir / "nonexistent.json"
        new_service._load_history()
        
        assert new_service.history == []
    
    def test_add_query_all_fields(self):
        query_id = self.service.add_query(
            query="Complex query",
            filepath="/path/to/file.xlsx",
            result_type="dataframe",
            success=True,
            execution_time=2.5,
            generated_code="result = df.groupby('col').mean()",
            error=None,
            result_shape=(50, 10)
        )
        
        entry = self.service.history[0]
        
        assert entry['query'] == "Complex query"
        assert entry['filepath'] == "/path/to/file.xlsx"
        assert entry['result_type'] == "dataframe"
        assert entry['success'] is True
        assert entry['execution_time_seconds'] == 2.5
        assert entry['generated_code'] == "result = df.groupby('col').mean()"
        assert entry['result_shape'] == (50, 10)