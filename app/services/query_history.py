"""
Query History Service for tracking user queries
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import uuid


class QueryHistory:
    """Service for managing query history"""
    
    def __init__(self):
        self.history_file = Path("data/query_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()
    
    def _load_history(self):
        """Load history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []
    
    def _save_history(self):
        """Save history to file"""
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
        """
        Add a query to history
        
        Args:
            query: User's natural language query
            filepath: Excel file path
            result_type: Type of result (dataframe, scalar, etc.)
            success: Whether query succeeded
            execution_time: Time taken in seconds
            generated_code: Generated pandas code
            error: Error message if failed
            result_shape: Shape of result DataFrame
            
        Returns:
            Query ID
        """
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
        """
        Get recent queries
        
        Args:
            limit: Maximum number of queries to return
            success_only: Only return successful queries
            
        Returns:
            List of recent queries
        """
        queries = self.history
        
        if success_only:
            queries = [q for q in queries if q.get('success', False)]
        
        # Sort by timestamp descending
        queries = sorted(queries, key=lambda x: x['timestamp'], reverse=True)
        
        return queries[:limit]
    
    def get_query_by_id(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific query by ID
        
        Args:
            query_id: Query ID
            
        Returns:
            Query entry or None
        """
        for entry in self.history:
            if entry['id'] == query_id:
                return entry
        return None
    
    def search_queries(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search queries by text
        
        Args:
            search_term: Text to search for
            limit: Maximum results
            
        Returns:
            Matching queries
        """
        results = []
        search_lower = search_term.lower()
        
        for entry in self.history:
            if search_lower in entry['query'].lower():
                results.append(entry)
        
        # Sort by timestamp descending
        results = sorted(results, key=lambda x: x['timestamp'], reverse=True)
        
        return results[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about query history
        
        Returns:
            Statistics dictionary
        """
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
        
        # Most common queries
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
        """Clear all history"""
        self.history = []
        self._save_history()
    
    def delete_query(self, query_id: str) -> bool:
        """
        Delete a specific query
        
        Args:
            query_id: Query ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        for i, entry in enumerate(self.history):
            if entry['id'] == query_id:
                self.history.pop(i)
                self._save_history()
                return True
        return False
    
    def export_history(self, filepath: Optional[str] = None) -> str:
        """
        Export history to JSON file
        
        Args:
            filepath: Output file path (auto-generated if None)
            
        Returns:
            Output file path
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/output/query_history_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
        
        return filepath