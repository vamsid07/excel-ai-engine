"""
API routes for Excel AI Engine
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
from pathlib import Path

router = APIRouter()


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
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            "status": "success",
            "message": "File uploaded successfully",
            "filename": file.filename,
            "filepath": file_path,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/query")
async def query_excel(
    filepath: str = Form(...),
    query: str = Form(...)
):
    """
    Execute a natural language query on Excel data
    
    Args:
        filepath: Path to the Excel file
        query: Natural language query describing the operation
    
    Returns:
        Query results
    """
    # This will be implemented in Day 2-3
    return {
        "status": "success",
        "message": "Query endpoint ready (to be implemented)",
        "filepath": filepath,
        "query": query,
        "note": "Full implementation coming in Day 2-3"
    }


@router.get("/operations")
async def list_supported_operations():
    """
    List all supported operations
    
    Returns:
        List of supported operations with examples
    """
    operations = {
        "basic_math": {
            "description": "Perform mathematical operations on columns",
            "examples": [
                "Add column A and column B",
                "Multiply salary by 1.1",
                "Calculate the difference between revenue and cost"
            ]
        },
        "aggregations": {
            "description": "Calculate summary statistics",
            "examples": [
                "Calculate average salary by department",
                "Find the sum of all sales",
                "Get min and max age"
            ]
        },
        "filtering": {
            "description": "Filter data based on conditions",
            "examples": [
                "Show all rows where salary > 50000",
                "Filter employees from Engineering department",
                "Get records where age is between 25 and 35"
            ]
        },
        "date_operations": {
            "description": "Work with date columns",
            "examples": [
                "Extract year from join_date",
                "Calculate days between two dates",
                "Filter records from last month"
            ]
        },
        "joining": {
            "description": "Join with another dataset",
            "examples": [
                "Inner join with another table on id",
                "Left join sales data with customer data"
            ]
        },
        "pivot": {
            "description": "Create pivot tables",
            "examples": [
                "Create pivot table with department as rows and average salary",
                "Pivot data by city and count"
            ]
        }
    }
    
    return {
        "status": "success",
        "supported_operations": operations,
        "total_operations": len(operations)
    }