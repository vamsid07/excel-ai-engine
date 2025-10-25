"""
Batch Processor for executing multiple queries
"""
import pandas as pd
from typing import List, Dict, Any
from app.services.llm_service import LLMService
from app.services.excel_service import ExcelService
import time


class BatchProcessor:
    """Service for batch query processing"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.excel_service = ExcelService()
    
    def process_batch(
        self,
        df: pd.DataFrame,
        queries: List[str],
        chain_results: bool = False
    ) -> Dict[str, Any]:
        """
        Process multiple queries in batch
        
        Args:
            df: Input DataFrame
            queries: List of queries to execute
            chain_results: If True, each query uses result of previous query
            
        Returns:
            Batch processing results
        """
        results = []
        current_df = df.copy()
        total_start = time.time()
        
        for i, query in enumerate(queries):
            query_start = time.time()
            
            try:
                # Get DataFrame info
                df_info = self.excel_service._extract_dataframe_info(current_df)
                
                # Generate code
                llm_response = self.llm_service.generate_pandas_code(
                    query=query,
                    df_info=df_info,
                    sheet_name="df"
                )
                
                if not llm_response['success']:
                    results.append({
                        'query_index': i,
                        'query': query,
                        'success': False,
                        'error': llm_response['error'],
                        'execution_time': time.time() - query_start
                    })
                    if not chain_results:
                        continue
                    else:
                        break  # Stop chain if query fails
                
                # Validate and execute
                code = self.llm_service.validate_and_enhance_code(llm_response['code'])
                execution_result = self.excel_service.execute_query_code(current_df, code)
                
                if not execution_result['success']:
                    results.append({
                        'query_index': i,
                        'query': query,
                        'success': False,
                        'error': execution_result['error'],
                        'execution_time': time.time() - query_start
                    })
                    if not chain_results:
                        continue
                    else:
                        break
                
                # Store result
                query_result = {
                    'query_index': i,
                    'query': query,
                    'success': True,
                    'generated_code': code,
                    'explanation': llm_response['explanation'],
                    'result_type': execution_result['result_type'],
                    'result_shape': execution_result.get('shape'),
                    'execution_time': time.time() - query_start
                }
                
                # For chaining, update current_df if result is a DataFrame
                if chain_results and execution_result['result_type'] == 'dataframe':
                    # Reconstruct DataFrame from result
                    current_df = pd.DataFrame(execution_result['result'])
                    query_result['chained'] = True
                else:
                    query_result['result'] = execution_result['result']
                    query_result['chained'] = False
                
                results.append(query_result)
                
            except Exception as e:
                results.append({
                    'query_index': i,
                    'query': query,
                    'success': False,
                    'error': str(e),
                    'execution_time': time.time() - query_start
                })
                if chain_results:
                    break
        
        total_time = time.time() - total_start
        
        return {
            'total_queries': len(queries),
            'successful_queries': sum(1 for r in results if r.get('success', False)),
            'failed_queries': sum(1 for r in results if not r.get('success', False)),
            'total_execution_time': round(total_time, 3),
            'chain_mode': chain_results,
            'results': results,
            'final_dataframe_shape': current_df.shape if chain_results else None
        }
    
    def execute_pipeline(
        self,
        df: pd.DataFrame,
        pipeline: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute a pipeline of operations with parameters
        
        Args:
            df: Input DataFrame
            pipeline: List of operations with parameters
                     [{'query': '...', 'export': True, 'filename': '...'}, ...]
            
        Returns:
            Pipeline execution results
        """
        current_df = df.copy()
        results = []
        
        for i, step in enumerate(pipeline):
            query = step.get('query')
            if not query:
                continue
            
            try:
                # Execute query
                df_info = self.excel_service._extract_dataframe_info(current_df)
                llm_response = self.llm_service.generate_pandas_code(query, df_info, "df")
                
                if not llm_response['success']:
                    results.append({
                        'step': i,
                        'query': query,
                        'success': False,
                        'error': llm_response['error']
                    })
                    break
                
                code = self.llm_service.validate_and_enhance_code(llm_response['code'])
                execution_result = self.excel_service.execute_query_code(current_df, code)
                
                if not execution_result['success']:
                    results.append({
                        'step': i,
                        'query': query,
                        'success': False,
                        'error': execution_result['error']
                    })
                    break
                
                # Update current DataFrame if result is DataFrame
                if execution_result['result_type'] == 'dataframe':
                    current_df = pd.DataFrame(execution_result['result'])
                
                results.append({
                    'step': i,
                    'query': query,
                    'success': True,
                    'result_type': execution_result['result_type'],
                    'result_shape': execution_result.get('shape')
                })
                
            except Exception as e:
                results.append({
                    'step': i,
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
                break
        
        return {
            'pipeline_steps': len(pipeline),
            'completed_steps': len(results),
            'success': all(r.get('success', False) for r in results),
            'results': results,
            'final_data': current_df.to_dict(orient='records') if len(current_df) <= 100 else None
        }