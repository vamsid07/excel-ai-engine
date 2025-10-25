# Day 3 Testing Guide - Advanced Features

## 🚀 Quick Start

```bash
# Install new dependencies
pip install -r requirements.txt

# Start server
python -m app.main

# Should see: "version": "3.0.0 - Day 3 Complete"
```

---

## Test 1: Join Operations

### Setup: Create Two Related Datasets

```bash
# Generate employees data
curl -X POST "http://localhost:8000/api/v1/generate-sample-data?rows=100"

# This creates data/output/sample_data.xlsx with employee information
```

Now create a second file (departments.xlsx) manually or use Python:

```python
import pandas as pd

# Create departments data
departments = pd.DataFrame({
    'department': ['Engineering', 'Sales', 'HR', 'Marketing', 'Finance'],
    'budget': [500000, 300000, 150000, 200000, 250000],
    'location': ['Building A', 'Building B', 'Building A', 'Building C', 'Building A']
})

departments.to_excel('data/input/departments.xlsx', index=False)
```

### Test Join

```bash
curl -X POST "http://localhost:8000/api/v1/join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "join_columns=department" \
  -F "how=inner" \
  -F "sheet1=Structured_Data"
```

### Test Join with Query

```bash
curl -X POST "http://localhost:8000/api/v1/query-with-join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "query=Show average salary by department with budget information" \
  -F "join_columns=department" \
  -F "sheet1=Structured_Data"
```

### Analyze Join Potential

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "sheet1=Structured_Data"
```

---

## Test 2: Export Functionality

### Export Query Result

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Filter employees with salary greater than 100000" \
  -F "output_filename=high_earners.xlsx" \
  -F "sheet_name=Structured_Data" \
  -F "formatted=true"
```

### Download Exported File

```bash
curl -O http://localhost:8000/api/v1/download/high_earners.xlsx
```

Or open in browser:
```
http://localhost:8000/api/v1/download/high_earners.xlsx
```

### List All Exports

```bash
curl "http://localhost:8000/api/v1/exports"
```

---

## Test 3: Batch Query Processing

### Simple Batch (Independent Queries)

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=["Calculate average salary", "Count employees by department", "Find maximum age"]' \
  -F "chain=false" \
  -F "sheet_name=Structured_Data"
```

### Chained Batch (Sequential Processing)

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=["Filter employees with salary > 80000", "Group by department and calculate average age", "Sort by average age descending"]' \
  -F "chain=true" \
  -F "sheet_name=Structured_Data"
```

---

## Test 4: Query History

### View Recent Queries

```bash
curl "http://localhost:8000/api/v1/history?limit=10"
```

### View Only Successful Queries

```bash
curl "http://localhost:8000/api/v1/history?limit=10&success_only=true"
```

### Get Specific Query by ID

```bash
# First get a query ID from history, then:
curl "http://localhost:8000/api/v1/history/YOUR-QUERY-ID-HERE"
```

### Search History

```bash
curl "http://localhost:8000/api/v1/history/search/salary?limit=20"
```

### Get Statistics

```bash
curl "http://localhost:8000/api/v1/history/stats"
```

### Clear History

```bash
curl -X DELETE "http://localhost:8000/api/v1/history"
```

---

## Test 5: Complex Workflows

### Workflow 1: Multi-File Analysis with Export

```bash
# Step 1: Upload files
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/output/sample_data.xlsx"

curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@data/input/departments.xlsx"

# Step 2: Join and query
curl -X POST "http://localhost:8000/api/v1/query-with-join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "query=Show employees in departments with budget > 200000, calculate average salary" \
  -F "join_columns=department" \
  -F "sheet1=Structured_Data"

# Step 3: Export result
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Filter employees with salary > 100000" \
  -F "output_filename=analysis_result.xlsx" \
  -F "sheet_name=Structured_Data"

# Step 4: Download
curl -O http://localhost:8000/api/v1/download/analysis_result.xlsx
```

### Workflow 2: Batch Processing Pipeline

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=[
    "Filter employees from Engineering or Sales department",
    "Calculate average salary and count by department",
    "Add a column showing percentage of total employees"
  ]' \
  -F "chain=true" \
  -F "sheet_name=Structured_Data"
```

---

## Test 6: Upload Multiple Files

```bash
curl -X POST "http://localhost:8000/api/v1/upload-multiple" \
  -F "files=@data/output/sample_data.xlsx" \
  -F "files=@data/input/departments.xlsx"
```

---

## Test Scenarios via Swagger UI

Open http://localhost:8000/docs

### Scenario 1: Complete Join Workflow
1. **POST /api/v1/analyze-join** - Analyze two files
2. **POST /api/v1/join** - Join them
3. **POST /api/v1/query-with-join** - Query the joined data
4. **POST /api/v1/export** - Export results

### Scenario 2: Batch Processing
1. **POST /api/v1/generate-sample-data** - Create data
2. **POST /api/v1/batch-query** - Run 3+ queries
3. **GET /api/v1/history** - View history
4. **GET /api/v1/history/stats** - Check statistics

### Scenario 3: Query, Export, Download
1. **POST /api/v1/query** - Run a complex query
2. **POST /api/v1/export** - Export the result
3. **GET /api/v1/exports** - List all exports
4. **GET /api/v1/download/{filename}** - Download

---

## Advanced Test Cases

### Test 1: Multi-File Join with Complex Query

```bash
curl -X POST "http://localhost:8000/api/v1/query-with-join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "query=Join the files, then show only employees in departments with budget > 200000, group by city and calculate average salary, and show top 5 cities" \
  -F "join_columns=department" \
  -F "how=left" \
  -F "sheet1=Structured_Data"
```

### Test 2: Chained Operations with Export

```bash
# Execute chain
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=[
    "Filter salary > 70000",
    "Calculate average age and salary by department",
    "Sort by average salary descending"
  ]' \
  -F "chain=true" \
  -F "sheet_name=Structured_Data"

# Then export final result
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Filter salary > 70000 and calculate average by department sorted by salary descending" \
  -F "output_filename=high_performers_analysis.xlsx" \
  -F "sheet_name=Structured_Data" \
  -F "formatted=true"
```

### Test 3: Query History Analysis

```bash
# Run several queries
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary" \
  -F "sheet_name=Structured_Data"

curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Count employees by department" \
  -F "sheet_name=Structured_Data"

curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Find top 10 highest paid employees" \
  -F "sheet_name=Structured_Data"

# Check statistics
curl "http://localhost:8000/api/v1/history/stats"

# Search history
curl "http://localhost:8000/api/v1/history/search/salary"
```

---

## Performance Tests

### Test Large Dataset

```bash
# Generate 10,000 rows
curl -X POST "http://localhost:8000/api/v1/generate-sample-data?rows=10000&include_unstructured=false"

# Complex query on large dataset
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Group by department and city, calculate average salary, min age, max age, count employees, then filter where count > 10" \
  -F "sheet_name=Structured_Data"
```

Expected: Should complete in < 5 seconds

### Test Batch Performance

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=[
    "Calculate average salary by department",
    "Calculate average age by department",
    "Count employees by city",
    "Find salary distribution percentiles",
    "Calculate correlation between age and salary"
  ]' \
  -F "chain=false" \
  -F "sheet_name=Structured_Data"
```

Expected: All 5 queries complete in < 15 seconds

---

## Error Handling Tests

### Test 1: Invalid Join Columns

```bash
curl -X POST "http://localhost:8000/api/v1/join" \
  -F "file1=data/output/sample_data.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "join_columns=nonexistent_column" \
  -F "sheet1=Structured_Data"
```

Expected: Clear error message about column not found

### Test 2: Export Non-DataFrame Result

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary" \
  -F "output_filename=test.xlsx" \
  -F "sheet_name=Structured_Data"
```

Expected: Error message explaining only DataFrames can be exported

### Test 3: Empty Batch

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=[]' \
  -F "sheet_name=Structured_Data"
```

Expected: Handles gracefully

---

## Integration Test Script

Save as `test_day3.sh`:

```bash
#!/bin/bash

echo "🧪 Day 3 Integration Tests"
echo "=========================="

BASE_URL="http://localhost:8000/api/v1"

echo ""
echo "1️⃣ Generating sample data..."
curl -s -X POST "$BASE_URL/generate-sample-data?rows=500" | jq -r '.status'

echo ""
echo "2️⃣ Testing simple query..."
curl -s -X POST "$BASE_URL/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary" \
  -F "sheet_name=Structured_Data" | jq -r '.status'

echo ""
echo "3️⃣ Testing export..."
curl -s -X POST "$BASE_URL/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Filter employees with age > 40" \
  -F "output_filename=test_export.xlsx" \
  -F "sheet_name=Structured_Data" | jq -r '.status'

echo ""
echo "4️⃣ Testing batch query..."
curl -s -X POST "$BASE_URL/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=["Calculate average salary", "Count by department"]' \
  -F "sheet_name=Structured_Data" | jq -r '.status'

echo ""
echo "5️⃣ Checking history..."
curl -s "$BASE_URL/history?limit=5" | jq -r '.status'

echo ""
echo "6️⃣ Getting statistics..."
curl -s "$BASE_URL/history/stats" | jq -r '.status'

echo ""
echo "7️⃣ Listing exports..."
curl -s "$BASE_URL/exports" | jq -r '.status'

echo ""
echo "✅ All tests completed!"
```

Make executable and run:
```bash
chmod +x test_day3.sh
./test_day3.sh
```

---

## Verification Checklist

After testing, verify:

```
✅ Join operations work with auto-detection
✅ Join operations work with specified columns
✅ Query-with-join executes successfully
✅ Export creates valid Excel files
✅ Downloaded files open correctly in Excel
✅ Formatted exports have styled headers
✅ Batch queries execute (chain=false)
✅ Chained queries execute (chain=true)
✅ Query history records all queries
✅ History search works
✅ Statistics calculate correctly
✅ Multiple file upload works
✅ All error cases handled gracefully
✅ Performance acceptable on large datasets
```

---

## Troubleshooting

### Issue: "File not found" errors
**Solution**: Check file paths are correct. Use full path or verify current directory.

### Issue: Join fails with auto-detection
**Solution**: Specify join columns explicitly with `join_columns` parameter.

### Issue: Export fails
**Solution**: Ensure query returns a DataFrame, not a scalar value.

### Issue: Batch queries slow
**Solution**: Reduce number of queries or use chain=true for sequential processing.

### Issue: History not persisting
**Solution**: Check `data/query_history.json` file permissions.

---

## Expected API Response Times

| Operation | Expected Time |
|-----------|--------------|
| Simple query | 1-2 seconds |
| Join (100 rows each) | 1-2 seconds |
| Join (1000 rows each) | 2-4 seconds |
| Export | 1-2 seconds |
| Batch (3 queries) | 3-6 seconds |
| Chained batch (3 queries) | 3-6 seconds |

Note: LLM calls add ~1-2 seconds overhead per query

---

## Next Steps

After successful Day 3 testing:

1. ✅ Push code to GitHub
2. ✅ Update README with Day 3 features
3. ✅ Prepare demo for recruiters
4. ✅ Document any edge cases found
5. ✅ Consider Day 4 enhancements (optional)

---

## Demo Script for Recruiters

```bash
# 1. Generate data
curl -X POST "http://localhost:8000/api/v1/generate-sample-data?rows=1000"

# 2. Show complex query capability
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Show top 10 highest paid employees in Engineering department, calculate their years of service, and group by city" \
  -F "sheet_name=Structured_Data"

# 3. Demonstrate batch processing
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=["Filter salary > 100000", "Group by department and calculate statistics", "Sort by average salary"]' \
  -F "chain=true" \
  -F "sheet_name=Structured_Data"

# 4. Export results
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Create a summary report with department-wise statistics" \
  -F "output_filename=executive_summary.xlsx" \
  -F "sheet_name=Structured_Data" \
  -F "formatted=true"

# 5. Show query history
curl "http://localhost:8000/api/v1/history/stats"
```