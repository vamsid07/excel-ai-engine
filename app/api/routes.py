from fastapi import APIRouter, UploadFile, File, HTTPException, Form, status
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
import os
from pathlib import Path
from app.services.llm_service import LLMService
from app.services.excel_service import ExcelService
from app.services.join_service import JoinService
from app.services.export_service import ExportService
from app.services.query_history import QueryHistory
from app.services.text_service import TextAnalysisService
import json
import time
import traceback
import re

router = APIRouter()

llm_service = LLMService()
excel_service = ExcelService()
join_service = JoinService()
export_service = ExportService()
query_history = QueryHistory()
text_service = TextAnalysisService()


def handle_error(error: Exception, operation: str) -> JSONResponse:
    error_message = str(error)
    error_type = type(error).__name__
    
    print(f"Error in {operation}: {error_type} - {error_message}")
    traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "operation": operation,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": time.time()
        }
    )


@router.post("/generate-sample-data")
async def generate_sample_data(
    rows: int = 1000,
    include_unstructured: bool = True
):
    try:
        if rows < 1 or rows > 100000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rows must be between 1 and 100,000"
            )
        
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
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "generate_sample_data")


@router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid file format. Only .xlsx, .xls, and .csv files supported"
            )
        
        Path("data/input").mkdir(parents=True, exist_ok=True)
        file_path = f"data/input/{file.filename}"
        
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty"
            )
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024
        if file_size > max_size:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum 50MB, uploaded {file_size / (1024*1024):.2f}MB"
            )
        
        sheets = excel_service.list_sheets(file_path)
        
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
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "upload_excel")


@router.post("/query")
async def query_excel(
    filepath: str = Form(...),
    query: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    start_time = time.time()
    
    try:
        if not filepath or not filepath.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filepath is required"
            )
        
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query is required"
            )
        
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filepath}"
            )
        
        try:
            df, df_info = excel_service.read_excel(filepath, sheet_name)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read Excel file: {str(e)}"
            )
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DataFrame is empty"
            )
        
        llm_response = llm_service.generate_pandas_code(
            query=query,
            df_info=df_info,
            sheet_name="df"
        )
        
        if not llm_response['success']:
            error_msg = llm_response.get('error', 'Unknown error')
            query_history.add_query(
                query=query,
                filepath=filepath,
                result_type="error",
                success=False,
                execution_time=time.time() - start_time,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Code generation failed: {error_msg}"
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code validation failed: {str(e)}"
            )
        
        execution_result = excel_service.execute_query_code(df, validated_code)
        
        execution_time = time.time() - start_time
        
        if not execution_result['success']:
            error_msg = execution_result.get('error', 'Unknown execution error')
            query_history.add_query(
                query=query,
                filepath=filepath,
                result_type="error",
                success=False,
                execution_time=execution_time,
                generated_code=validated_code,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Execution failed: {error_msg}"
            )
        
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
        return handle_error(e, "query_excel")


@router.post("/join")
async def join_files(
    file1: str = Form(...),
    file2: str = Form(...),
    join_columns: Optional[str] = Form(None),
    how: str = Form("inner"),
    sheet1: Optional[str] = Form(None),
    sheet2: Optional[str] = Form(None)
):
    try:
        if not os.path.exists(file1):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First file not found: {file1}"
            )
        if not os.path.exists(file2):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Second file not found: {file2}"
            )
        
        if how not in ['inner', 'left', 'right', 'outer']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid join type: {how}. Must be one of: inner, left, right, outer"
            )
        
        df1, info1 = excel_service.read_excel(file1, sheet1)
        df2, info2 = excel_service.read_excel(file2, sheet2)
        
        join_cols = None
        if join_columns:
            join_cols = [col.strip() for col in join_columns.split(',')]
        
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
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "join_files")


@router.post("/export")
async def export_result(
    filepath: str = Form(...),
    query: str = Form(...),
    output_filename: Optional[str] = Form(None),
    sheet_name: Optional[str] = Form(None),
    formatted: bool = Form(False)
):
    try:
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filepath}"
            )
        
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        llm_response = llm_service.generate_pandas_code(query, df_info, "df")
        if not llm_response['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Code generation failed: {llm_response['error']}"
            )
        
        code = llm_service.validate_and_enhance_code(llm_response['code'])
        execution_result = excel_service.execute_query_code(df, code)
        
        if not execution_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query execution failed: {execution_result['error']}"
            )
        
        if execution_result['result_type'] == 'dataframe':
            import pandas as pd
            result_df = pd.DataFrame(execution_result['result'])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Query result is not a DataFrame. Cannot export non-tabular results."
            )
        
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
        return handle_error(e, "export_result")


@router.post("/query-join")
async def query_join(
    query: str = Form(...),
    file1: str = Form(...),
    file2: str = Form(...),
    sheet1: Optional[str] = Form(None),
    sheet2: Optional[str] = Form(None)
):
    start_time = time.time()
    
    try:
        if not os.path.exists(file1):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"First file not found: {file1}"
            )
        if not os.path.exists(file2):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Second file not found: {file2}"
            )
        
        df1, info1 = excel_service.read_excel(file1, sheet1)
        df2, info2 = excel_service.read_excel(file2, sheet2)
        
        join_type = 'inner'
        query_lower = query.lower()
        if 'left join' in query_lower or 'left outer' in query_lower:
            join_type = 'left'
        elif 'right join' in query_lower or 'right outer' in query_lower:
            join_type = 'right'
        elif 'outer join' in query_lower or 'full outer' in query_lower or 'full join' in query_lower:
            join_type = 'outer'
        
        join_columns = None
        on_pattern = r'on\s+(\w+)'
        on_match = re.search(on_pattern, query_lower)
        if on_match:
            join_col = on_match.group(1)
            for col in info1['columns']:
                if join_col in col.lower():
                    join_columns = [col]
                    break
        
        if not join_columns:
            using_pattern = r'using\s+(\w+)'
            using_match = re.search(using_pattern, query_lower)
            if using_match:
                join_col = using_match.group(1)
                for col in info1['columns']:
                    if join_col in col.lower():
                        join_columns = [col]
                        break
        
        result_df = join_service.smart_join(df1, df2, join_columns, join_type)
        
        execution_time = time.time() - start_time
        
        return {
            "status": "success",
            "query": query,
            "file1": file1,
            "file2": file2,
            "join_type": join_type,
            "join_columns": join_columns or join_service._detect_join_columns(df1, df2),
            "input_shapes": {
                "file1": info1['shape'],
                "file2": info2['shape']
            },
            "result_shape": result_df.shape,
            "result": result_df.head(100).to_dict(orient='records'),
            "result_columns": result_df.columns.tolist(),
            "execution_time_seconds": round(execution_time, 3)
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "query_join")
    

@router.post("/analyze-text")
async def analyze_text(
    filepath: str = Form(...),
    column: str = Form(...),
    analysis_type: str = Form("sentiment"),
    sheet_name: Optional[str] = Form(None)
):
    try:
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filepath}"
            )
        
        valid_types = ['sentiment', 'summary', 'keywords', 'length', 'word_count']
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
            )
        
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        if column not in df.columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Column '{column}' not found. Available columns: {', '.join(df.columns)}"
            )
        
        result_df = text_service.analyze_text_column(df, column, analysis_type)
        
        return {
            "status": "success",
            "filepath": filepath,
            "column": column,
            "analysis_type": analysis_type,
            "result_shape": result_df.shape,
            "result": result_df.head(100).to_dict(orient='records'),
            "new_columns": [col for col in result_df.columns if col not in df.columns]
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "analyze_text")


@router.get("/download/{filename}")
async def download_file(filename: str):
    try:
        file_path = Path("data/output") / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filename}"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "download_file")


@router.post("/analyze")
async def analyze_excel(
    filepath: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    try:
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filepath}"
            )
        
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        stats_dict = {}
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                stats_df = df[numeric_cols].describe()
                stats_dict = stats_df.to_dict()
            else:
                stats_dict = {"message": "No numeric columns available"}
        except Exception:
            stats_dict = {"error": "Statistics not available"}
        
        return {
            "status": "success",
            "filepath": filepath,
            "analysis": {
                "shape": df_info['shape'],
                "columns": df_info['columns'],
                "data_types": dict(zip(df_info['columns'], df_info['dtypes'])),
                "null_counts": df_info['null_counts'],
                "has_duplicates": df_info['has_duplicates'],
                "memory_usage_bytes": int(df_info['memory_usage']),
                "sample_data": df.head(5).to_dict(orient='records'),
                "statistics": stats_dict
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "analyze_excel")


@router.get("/sheets/{filepath:path}")
async def list_sheets(filepath: str):
    try:
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {filepath}"
            )
        
        sheets = excel_service.list_sheets(filepath)
        
        return {
            "status": "success",
            "filepath": filepath,
            "sheets": sheets,
            "count": len(sheets)
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "list_sheets")


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    success_only: bool = False
):
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        history = query_history.get_recent_queries(limit, success_only)
        return {
            "status": "success",
            "history": history,
            "count": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        return handle_error(e, "get_query_history")


@router.get("/history/stats")
async def get_history_statistics():
    try:
        stats = query_history.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        return handle_error(e, "get_history_statistics")


@router.get("/health")
async def health_check():
    try:
        llm_status = "operational"
        try:
            import requests
            response = requests.get(f"{llm_service.ollama_url}/api/tags", timeout=5)
            llm_status = "operational" if response.status_code == 200 else "error"
        except Exception:
            llm_status = "error"
        
        return {
            "status": "healthy",
            "services": {
                "api": "operational",
                "llm": llm_status,
                "excel_processing": "operational",
                "join_service": "operational",
                "export_service": "operational",
                "query_history": "operational"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }