"""
API routes for Excel AI Engine - Day 2 Implementation
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
from pathlib import Path
from app.services.llm_service import LLMService
from app.services.excel_service import ExcelService
import json

router = APIRouter()

# Initialize services
llm_service = LLMService()
excel_service = ExcelService()


@router.post("/generate-sample-data")
async def generate_sample_data(
    rows: int = 1000,
    include_unstructured: bool = True
):
    """
    Generate sample Excel data for testing
    
    Args:
        rows: Number of rows to generate
        include_unstructured: Whether to include unstructured data sheet
    
    Returns:
        Success message with file path
    """
    try:
        from app.utils.data_generator import DataGenerator
        
        generator = DataGenerator()
        
        # Generate structured data
        structured_df = generator.generate_structured_data(rows=rows)
        
        # Generate unstructured data if requested
        unstructured_df = None
        if include_unstructured:
            unstructured_df = generator.generate_unstructured_data(rows=rows)
        
        # Save to Excel
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
    """
    Upload an Excel file for processing
    
    Args:
        file: Excel file to upload
    
    Returns:
        File info and upload status
    """
    try:
        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file format. Only .xlsx and .xls files are supported"
            )
        
        # Create input directory if it doesn't exist
        Path("data/input").mkdir(parents=True, exist_ok=True)
        
        # Save the file
        file_path = f"data/input/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Read and analyze the file
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


@router.post("/query")
async def query_excel(
    filepath: str = Form(...),
    query: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    """
    Execute a natural language query on Excel data using AI
    
    Args:
        filepath: Path to the Excel file
        query: Natural language query describing the operation
        sheet_name: Optional sheet name (defaults to first sheet)
    
    Returns:
        Query results with generated code and explanation
    """
    try:
        # Validate file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
        
        # Read Excel file
        df, df_info = excel_service.read_excel(filepath, sheet_name)
        
        # Generate pandas code using LLM
        llm_response = llm_service.generate_pandas_code(
            query=query,
            df_info=df_info,
            sheet_name="df"
        )
        
        if not llm_response['success']:
            raise HTTPException(
                status_code=500, 
                detail=f"LLM generation failed: {llm_response['error']}"
            )
        
        # Validate the generated code
        try:
            validated_code = llm_service.validate_and_enhance_code(llm_response['code'])
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Code validation failed: {str(e)}")
        
        # Execute the code
        execution_result = excel_service.execute_query_code(df, validated_code)
        
        if not execution_result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Execution failed: {execution_result['error']}"
            )
        
        # Prepare response
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
            "truncated": execution_result.get('truncated', False)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution error: {str(e)}")


@router.post("/analyze")
async def analyze_excel(
    filepath: str = Form(...),
    sheet_name: Optional[str] = Form(None)
):
    """
    Get detailed analysis of an Excel file
    
    Args:
        filepath: Path to the Excel file
        sheet_name: Optional sheet name
    
    Returns:
        Comprehensive data analysis
    """
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
    """
    List all sheets in an Excel file
    
    Args:
        filepath: Path to Excel file
    
    Returns:
        List of sheet names
    """
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
    """
    List all supported operations with examples
    
    Returns:
        Comprehensive list of operations
    """
    operations = {
        "basic_math": {
            "description": "Perform mathematical operations on columns",
            "examples": [
                "Add salary and bonus columns",
                "Multiply price by 1.15 for new column",
                "Calculate profit margin (revenue - cost) / revenue",
                "Square root of all values in column"
            ],
            "capabilities": [
                "Addition, subtraction, multiplication, division",
                "Complex formulas with multiple columns",
                "Mathematical functions (sqrt, log, exp, etc.)",
                "Conditional calculations"
            ]
        },
        "aggregations": {
            "description": "Calculate summary statistics and groupby operations",
            "examples": [
                "Calculate average salary by department",
                "Sum of sales grouped by region and product",
                "Count of employees per city",
                "Find min, max, median, std deviation",
                "Multiple aggregations: sum, mean, count together"
            ],
            "capabilities": [
                "Single and multiple groupby columns",
                "Multiple aggregation functions",
                "Custom aggregations",
                "Percentiles and quantiles"
            ]
        },
        "filtering": {
            "description": "Filter data based on any conditions",
            "examples": [
                "Show all rows where salary > 50000",
                "Filter employees from Engineering AND age < 35",
                "Get records where city is Mumbai or Delhi",
                "Complex conditions: (age > 30 AND salary > 60000) OR department is 'Sales'",
                "Filter by date range: join_date between 2020 and 2023"
            ],
            "capabilities": [
                "Single and multiple conditions",
                "AND, OR, NOT logic",
                "Comparison operators (>, <, >=, <=, ==, !=)",
                "String operations (contains, startswith, endswith)",
                "Date comparisons"
            ]
        },
        "date_operations": {
            "description": "Work with date and time columns",
            "examples": [
                "Extract year, month, day from date column",
                "Calculate age from birthdate",
                "Find difference in days between two dates",
                "Filter records from last 30 days",
                "Group by month and year",
                "Calculate tenure in years"
            ],
            "capabilities": [
                "Date extraction (year, month, day, weekday)",
                "Date arithmetic (difference, addition)",
                "Date filtering and comparisons",
                "Convert string to datetime",
                "Time-based grouping"
            ]
        },
        "pivot": {
            "description": "Create and manipulate pivot tables",
            "examples": [
                "Pivot table with department as rows and average salary",
                "Multi-level pivot: region and department vs product sales",
                "Unpivot table back to long format",
                "Cross-tabulation of two categorical variables"
            ],
            "capabilities": [
                "Single and multi-index pivots",
                "Multiple value columns",
                "Different aggregation functions",
                "Pivot and unpivot operations"
            ]
        },
        "joining": {
            "description": "Merge datasets together",
            "examples": [
                "Inner join two tables on employee_id",
                "Left join to keep all records from first table",
                "Join on multiple columns",
                "Concatenate tables vertically"
            ],
            "capabilities": [
                "Inner, left, right, outer joins",
                "Single and multiple key joins",
                "Vertical concatenation",
                "Merge with indicator column"
            ]
        },
        "sorting": {
            "description": "Sort data by columns",
            "examples": [
                "Sort by salary descending",
                "Sort by department then salary",
                "Get top 10 highest paid employees"
            ]
        },
        "text_operations": {
            "description": "String manipulation and analysis",
            "examples": [
                "Convert names to uppercase",
                "Extract first name from full name",
                "Count words in text column",
                "Check if email contains domain",
                "Concatenate first and last name"
            ]
        },
        "statistical": {
            "description": "Advanced statistical operations",
            "examples": [
                "Calculate correlation between columns",
                "Find outliers using IQR method",
                "Normalize values to 0-1 range",
                "Calculate z-scores",
                "Moving averages"
            ]
        }
    }
    
    return {
        "status": "success",
        "message": "This AI system can handle ANY query! These are just examples.",
        "supported_operations": operations,
        "total_categories": len(operations),
        "note": "The LLM can understand and execute queries beyond these examples. Try anything!"
    }


@router.get("/health")
async def health_check():
    """Check if services are operational"""
    try:
        # Test LLM connection
        test_response = llm_service.client.models.list()
        llm_status = "operational"
    except:
        llm_status = "error"
    
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "llm": llm_status,
            "excel_processing": "operational"
        },
        "version": "2.0.0"
    }