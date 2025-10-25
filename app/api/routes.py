"""
API routes for Excel AI Engine - Day 3 Complete Implementation
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional, List
import os
from pathlib import Path
from app.services.llm_service import LLMService
from app.services.excel_service import ExcelService
from app.services.join_service import JoinService
from app.services.export_service import ExportService
from app.services.query_history import QueryHistory
from app.services.batch_processor import BatchProcessor
import json
import time

router = APIRouter()

# Initialize services
llm_service = LLMService()
excel_service = ExcelService()
join_service = JoinService()
export_service = ExportService()
query_history = QueryHistory()
batch_processor = BatchProcessor()


@router.post("/generate-sample-data")
async def generate_sample_data(
    rows: int = 1000,
    include_unstructured: bool = True
):
    """Generate sample Excel data for testing"""
    try:
        from app.utils.data_generator import DataGenerator
        
        generator = DataGenerator()
        structured_df = generator.generate_structured_data(rows=rows)
        unstructured_df = None
        if include_unstructured:
            unstructured_df = generator.generate_unstructured_data(rows=rows)
        
        filepath = generator.save_to_excel(
            structured_df, 
            unstructured_df,
            filepath="data/output/sample_data.xlsx"
        )
        
        return {
            "status": "success",
            "message": "Sample data generated successfully",
            "filepath": filepath,
            "rows_generated": rows,
            "sheets": ["Structured_Data"] + (["Unstructured_Data"] if include_unstructured else [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating data: {str(e)}")


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    """Upload an Excel file for processing"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file format. Only .xlsx and .xls files are supported"
            )
        
        Path("data/input").mkdir(parents=True, exist_ok=True)
        file_path = f"data/input/{file.filename}"
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        sheets = excel_service.list_sheets(file_path)
        file_size = os.path.getsize(file_path)
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "filename": file.filename,
            "filepath": file_path,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "sheets": sheets,
            "sheet_count": len(sheets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """Upload multiple Excel files for joining"""
    try:
        uploaded_files = []
        
        for file in files:
            if not file.filename.endswith(('.xlsx', '.xls')):
                continue
            
            Path("data/input").mkdir(parents=True, exist_ok=True)
            file_path = f"data/input/{file.filename}"
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            sheets = excel_service.list_sheets(file_path)
            
            uploaded_files.append({
                "filename": file.filename,
                "filepath": file_path,
                "sheets": sheets
            })
        
        return {
            "status": "success",
            "message": f"Uploaded {len(uploaded_files)} files",
            "files": uploaded_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")


@router.post("/query")
async def query_excel(
    filepath: str = Form(...),
    query: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    """Execute a natural language query on Excel data using AI"""
    start_time = time.time()
    
    try:
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        llm_response = llm_service.generate_pandas_code(
            query=query,
            df_info=df_info,
            sheet_name="df"
        )
        
        if not llm_response['success']:
            query_history.add_query(
                query=query,
                filepath=filepath,
                result_type="error",
                success=False,
                execution_time=time.time() - start_time,
                error=llm_response['error']
            )
            raise HTTPException(
                status_code=500, 
                detail=f"LLM generation failed: {llm_response['error']}"
            )
        
        try:
            validated_code = llm_service.validate_and_enhance_code(llm_response['code'])
        except ValueError as e:
            query_history.add_query(
                query=query,
                filepath=filepath,
                result_type="error",
                success=False,
                execution_time=time.time() - start_time,
                error=str(e)
            )
            raise HTTPException(status_code=400, detail=f"Code validation failed: {str(e)}")
        
        execution_result = excel_service.execute_query_code(df, validated_code)
        
        execution_time = time.time() - start_time
        
        if not execution_result['success']:
            query_history.add_query(
                query=query,
                filepath=filepath,
                result_type="error",
                success=False,
                execution_time=execution_time,
                generated_code=validated_code,
                error=execution_result['error']
            )
            raise HTTPException(
                status_code=500,
                detail=f"Execution failed: {execution_result['error']}"
            )
        
        # Add to history
        query_history.add_query(
            query=query,
            filepath=filepath,
            result_type=execution_result['result_type'],
            success=True,
            execution_time=execution_time,
            generated_code=validated_code,
            result_shape=execution_result.get('shape')
        )
        
        return {
            "status": "success",
            "query": query,
            "filepath": filepath,
            "sheet_name": df_info['sheet_name'],
            "data_shape": df_info['shape'],
            "generated_code": validated_code,
            "explanation": llm_response['explanation'],
            "operation_type": llm_response['operation_type'],
            "result": execution_result['result'],
            "result_type": execution_result['result_type'],
            "result_shape": execution_result.get('shape'),
            "columns": execution_result.get('columns'),
            "truncated": execution_result.get('truncated', False),
            "execution_time_seconds": round(execution_time, 3)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")


@router.post("/join")
async def join_files(
    file1: str = Form(...),
    file2: str = Form(...),
    join_columns: Optional[str] = Form(None),
    how: str = Form("inner"),
    sheet1: Optional[str] = Form(None),
    sheet2: Optional[str] = Form(None)
):
    """Join two Excel files"""
    try:
        # Load files
        df1, info1 = excel_service.read_excel(file1, sheet1)
        df2, info2 = excel_service.read_excel(file2, sheet2)
        
        # Parse join columns
        join_cols = None
        if join_columns:
            join_cols = [col.strip() for col in join_columns.split(',')]
        
        # Perform join
        result_df = join_service.smart_join(df1, df2, join_cols, how)
        
        return {
            "status": "success",
            "file1": file1,
            "file2": file2,
            "join_type": how,
            "join_columns": join_cols or join_service._detect_join_columns(df1, df2),
            "input_shapes": {
                "file1": info1['shape'],
                "file2": info2['shape']
            },
            "result_shape": result_df.shape,
            "result": result_df.head(100).to_dict(orient='records'),
            "result_columns": result_df.columns.tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Join failed: {str(e)}")


@router.post("/query-with-join")
async def query_with_join(
    file1: str = Form(...),
    file2: str = Form(...),
    query: str = Form(...),
    join_columns: Optional[str] = Form(None),
    how: str = Form("inner"),
    sheet1: Optional[str] = Form(None),
    sheet2: Optional[str] = Form(None)
):
    """Join two files and execute a query on the result"""
    try:
        # Load and join files
        df1, _ = excel_service.read_excel(file1, sheet1)
        df2, _ = excel_service.read_excel(file2, sheet2)
        
        join_cols = None
        if join_columns:
            join_cols = [col.strip() for col in join_columns.split(',')]
        
        joined_df = join_service.smart_join(df1, df2, join_cols, how)
        
        # Execute query on joined data
        df_info = excel_service._extract_dataframe_info(joined_df)
        
        llm_response = llm_service.generate_pandas_code(query, df_info, "df")
        
        if not llm_response['success']:
            raise HTTPException(status_code=500, detail=llm_response['error'])
        
        code = llm_service.validate_and_enhance_code(llm_response['code'])
        execution_result = excel_service.execute_query_code(joined_df, code)
        
        if not execution_result['success']:
            raise HTTPException(status_code=500, detail=execution_result['error'])
        
        return {
            "status": "success",
            "join_info": {
                "file1": file1,
                "file2": file2,
                "join_type": how,
                "joined_shape": joined_df.shape
            },
            "query": query,
            "generated_code": code,
            "explanation": llm_response['explanation'],
            "result": execution_result['result'],
            "result_type": execution_result['result_type']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Join query failed: {str(e)}")


@router.post("/analyze-join")
async def analyze_join_potential(
    file1: str = Form(...),
    file2: str = Form(...),
    sheet1: Optional[str] = Form(None),
    sheet2: Optional[str] = Form(None)
):
    """Analyze potential for joining two files"""
    try:
        df1, _ = excel_service.read_excel(file1, sheet1)
        df2, _ = excel_service.read_excel(file2, sheet2)
        
        analysis = join_service.analyze_join_potential(df1, df2)
        
        return {
            "status": "success",
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/export")
async def export_result(
    filepath: str = Form(...),
    query: str = Form(...),
    output_filename: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
    formatted: bool = Form(False)
):
    """Execute query and export result to new Excel file"""
    try:
        # Execute query
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        llm_response = llm_service.generate_pandas_code(query, df_info, "df")
        if not llm_response['success']:
            raise HTTPException(status_code=500, detail=llm_response['error'])
        
        code = llm_service.validate_and_enhance_code(llm_response['code'])
        execution_result = excel_service.execute_query_code(df, code)
        
        if not execution_result['success']:
            raise HTTPException(status_code=500, detail=execution_result['error'])
        
        # Convert result to DataFrame
        if execution_result['result_type'] == 'dataframe':
            import pandas as pd
            result_df = pd.DataFrame(execution_result['result'])
        else:
            raise HTTPException(
                status_code=400, 
                detail="Query result is not a DataFrame. Only DataFrame results can be exported."
            )
        
        # Export
        if formatted:
            output_path = export_service.export_with_formatting(
                result_df, 
                output_filename or "query_result.xlsx",
                sheet_name="Result"
            )
        else:
            output_path = export_service.export_to_excel(
                result_df,
                output_filename,
                sheet_name="Result"
            )
        
        summary = export_service.get_export_summary(result_df)
        
        return {
            "status": "success",
            "message": "Query executed and result exported",
            "query": query,
            "output_file": output_path,
            "summary": summary,
            "download_url": f"/api/v1/download/{Path(output_path).name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download an exported file"""
    try:
        file_path = Path("data/output") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/exports")
async def list_exports():
    """List all exported files"""
    try:
        exports = export_service.list_exports()
        return {
            "status": "success",
            "exports": exports,
            "count": len(exports)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing exports: {str(e)}")


@router.post("/batch-query")
async def batch_query(
    filepath: str = Form(...),
    queries: str = Form(...),
    chain: bool = Form(False),
    sheet_name: Optional[str] = Form(None)
):
    """Execute multiple queries in batch"""
    try:
        # Parse queries (expects JSON array)
        query_list = json.loads(queries)
        
        if not isinstance(query_list, list):
            raise HTTPException(status_code=400, detail="Queries must be a JSON array")
        
        df, _ = excel_service.read_excel(filepath, sheet_name)
        
        result = batch_processor.process_batch(df, query_list, chain_results=chain)
        
        return {
            "status": "success",
            "batch_result": result
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in queries parameter")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    success_only: bool = False
):
    """Get recent query history"""
    try:
        history = query_history.get_recent_queries(limit, success_only)
        return {
            "status": "success",
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.get("/history/{query_id}")
async def get_query_by_id(query_id: str):
    """Get specific query by ID"""
    try:
        query = query_history.get_query_by_id(query_id)
        if query is None:
            raise HTTPException(status_code=404, detail="Query not found")
        return {
            "status": "success",
            "query": query
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/history/search/{search_term}")
async def search_history(search_term: str, limit: int = 20):
    """Search query history"""
    try:
        results = query_history.search_queries(search_term, limit)
        return {
            "status": "success",
            "search_term": search_term,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/history/stats")
async def get_history_statistics():
    """Get query history statistics"""
    try:
        stats = query_history.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/history")
async def clear_history():
    """Clear all query history"""
    try:
        query_history.clear_history()
        return {
            "status": "success",
            "message": "Query history cleared"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/analyze")
async def analyze_excel(
    filepath: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    """Get detailed analysis of an Excel file"""
    try:
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        return {
            "status": "success",
            "filepath": filepath,
            "analysis": {
                "shape": df_info['shape'],
                "columns": df_info['columns'],
                "data_types": dict(zip(df_info['columns'], df_info['dtypes'])),
                "null_counts": df_info['null_counts'],
                "has_duplicates": df_info['has_duplicates'],
                "memory_usage_bytes": df_info['memory_usage'],
                "sample_data": df_info['sample_data'],
                "statistics": df_info['statistics']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.get("/sheets/{filepath:path}")
async def list_sheets(filepath: str):
    """List all sheets in an Excel file"""
    try:
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        sheets = excel_service.list_sheets(filepath)
        
        return {
            "status": "success",
            "filepath": filepath,
            "sheets": sheets,
            "count": len(sheets)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing sheets: {str(e)}")


@router.get("/operations")
async def list_supported_operations():
    """List all supported operations with examples"""
    operations = {
        "basic_operations": {
            "query": "Simple queries on single files",
            "join": "Merge multiple Excel files",
            "export": "Save query results to new files",
            "batch": "Execute multiple queries at once"
        },
        "examples": {
            "aggregation": "Calculate average salary by department",
            "filtering": "Show employees with salary > 100000",
            "join": "Join sales.xlsx with customers.xlsx on customer_id",
            "export": "Filter data and export to high_performers.xlsx",
            "batch": "Filter, then group, then sort - all in one request"
        }
    }
    
    return {
        "status": "success",
        "message": "This AI system can handle ANY query!",
        "operations": operations
    }


@router.get("/health")
async def health_check():
    """Check if services are operational"""
    try:
        llm_status = "operational" if llm_service else "error"
    except:
        llm_status = "error"
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "llm": llm_status,
            "excel_processing": "operational",
            "join_service": "operational",
            "export_service": "operational",
            "query_history": "operational",
            "batch_processor": "operational"
        },
        "version": "3.0.0 - Day 3 Complete"
    }