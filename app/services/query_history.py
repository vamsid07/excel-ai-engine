from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import uuid


class QueryHistory:
    def __init__(self):
        self.history_file = Path("data/query_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()
    
    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []
    
    def _save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    def add_query(
        self,
        query: str,
        filepath: str,
        result_type: str,
        success: bool,
        execution_time: float,
        generated_code: Optional[str] = None,
        error: Optional[str] = None,
        result_shape: Optional[tuple] = None
    ) -> str:
        query_id = str(uuid.uuid4())
        
        entry = {
            'id': query_id,
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'filepath': filepath,
            'result_type': result_type,
            'success': success,
            'execution_time_seconds': round(execution_time, 3),
            'generated_code': generated_code,
            'error': error,
            'result_shape': result_shape
        }
        
        self.history.append(entry)
        self._save_history()
        
        return query_id
    
    def get_recent_queries(
        self,
        limit: int = 10,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:

        queries = self.history
        
        if success_only:
            queries = [q for q in queries if q.get('success', False)]
        queries = sorted(queries, key=lambda x: x['timestamp'], reverse=True)
        
        return queries[:limit]
    
    def get_query_by_id(self, query_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.history:
            if entry['id'] == query_id:
                return entry
        return None
    
    def search_queries(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        results = []
        search_lower = search_term.lower()
        
        for entry in self.history:
            if search_lower in entry['query'].lower():
                results.append(entry)
        results = sorted(results, key=lambda x: x['timestamp'], reverse=True)
        
        return results[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        if not self.history:
            return {
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'success_rate': 0,
                'avg_execution_time': 0
            }
        
        total = len(self.history)
        successful = sum(1 for q in self.history if q.get('success', False))
        failed = total - successful
        
        execution_times = [
            q.get('execution_time_seconds', 0) 
            for q in self.history 
            if q.get('success', False)
        ]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0
        query_counts = {}
        for entry in self.history:
            query = entry['query']
            query_counts[query] = query_counts.get(query, 0) + 1
        
        top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_queries': total,
            'successful_queries': successful,
            'failed_queries': failed,
            'success_rate': round(successful / total * 100, 2) if total > 0 else 0,
            'avg_execution_time_seconds': round(avg_time, 3),
            'top_queries': [{'query': q, 'count': c} for q, c in top_queries]
        }
    
    def clear_history(self):
        self.history = []
        self._save_history()
    
    def delete_query(self, query_id: str) -> bool:
        for i, entry in enumerate(self.history):
            if entry['id'] == query_id:
                self.history.pop(i)
                self._save_history()
                return True
        return False
    
    def export_history(self, filepath: Optional[str] = None) -> str:
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/output/query_history_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
        
        return filepath