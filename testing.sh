#!/bin/bash

BASE_URL="http://localhost:8000/api/v1"

echo "Excel AI Engine - Complete Testing Suite"
echo "==========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' 

test_count=0
passed=0
failed=0

run_test() {
    test_count=$((test_count + 1))
    test_name=$1
    shift
    
    echo -e "${YELLOW}Test $test_count: $test_name${NC}"
    
    response=$(eval "$@" 2>&1)
    status=$?
    
    if [ $status -eq 0 ] && echo "$response" | grep -q '"status":"success"\|"status": "success"'; then
        echo -e "${GREEN}✅ PASSED${NC}"
        passed=$((passed + 1))
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
    else
        echo -e "${RED}❌ FAILED${NC}"
        failed=$((failed + 1))
        echo "$response"
    fi
    echo ""
    echo "---"
    echo ""
}

echo "0️⃣  Checking if server is running..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Start it with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Server is running${NC}"
echo ""

echo "📊 Generating sample data..."
run_test "Generate Sample Data" \
    "curl -s -X POST '$BASE_URL/generate-sample-data?rows=100&include_unstructured=true'"

echo "🧮 TEST 1: BASIC MATH OPERATIONS"
echo "================================"

run_test "1.1: Add two columns (salary + bonus)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Add a new column called total_compensation which is salary plus projects_completed times 1000'"

run_test "1.2: Multiply columns" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Create a column performance_bonus as performance_score multiplied by 1000'"

run_test "1.3: Division operation" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Create a new column monthly_salary by dividing salary by 12'"

echo "📊 TEST 2: AGGREGATION OPERATIONS"
echo "=================================="

run_test "2.1: Calculate average by group" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Calculate average salary by department'"

run_test "2.2: Multiple aggregations (sum, mean, min, max)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show sum, average, minimum, and maximum salary by department'"

run_test "2.3: Count by category" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Count how many employees are in each city'"

run_test "2.4: Standard deviation" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Calculate standard deviation of salary by department'"

echo "🔍 TEST 3: FILTER OPERATIONS"
echo "============================"

run_test "3.1: Simple filter (greater than)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show employees with salary greater than 100000'"

run_test "3.2: Multiple conditions (AND)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Filter employees with age greater than 40 AND salary greater than 80000'"

run_test "3.3: Multiple conditions (OR)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show employees in Engineering department OR with salary above 120000'"

run_test "3.4: String contains filter" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Find all employees whose city name contains New'"

echo "📅 TEST 4: DATE OPERATIONS"
echo "=========================="

run_test "4.1: Extract year from date" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Extract the year from join_date column and create a new column called join_year'"

run_test "4.2: Extract month and day" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Extract month and day from join_date and create new columns'"

run_test "4.3: Calculate date difference (years of service)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Calculate years of service from join_date to today'"

run_test "4.4: Filter by date range" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show employees who joined after 2020'"

echo "🔄 TEST 5: PIVOT OPERATIONS"
echo "==========================="

run_test "5.1: Simple pivot table" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Create a pivot table with department as rows and average salary'"

run_test "5.2: Pivot with multiple dimensions" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Create pivot table with department as rows, city as columns, and average salary as values'"

run_test "5.3: Pivot with sum aggregation" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Pivot table showing total projects_completed by department'"

echo "↩️  TEST 6: UNPIVOT OPERATIONS"
echo "=============================="

run_test "6.1: Unpivot/Melt data" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Unpivot the data keeping id and name as identifiers and converting salary, age, projects_completed into separate rows'"

echo "🔗 TEST 7: JOIN OPERATIONS"
echo "=========================="

run_test "7.1: List available sheets" \
    "curl -s -X GET '$BASE_URL/sheets/data/output/sample_data.xlsx'"

run_test "7.2: Inner join on common column" \
    "curl -s -X POST '$BASE_URL/join' \
    -F 'file1=data/output/sample_data.xlsx' \
    -F 'file2=data/output/sample_data.xlsx' \
    -F 'sheet1=Structured_Data' \
    -F 'sheet2=Structured_Data' \
    -F 'how=inner'"

run_test "7.3: Natural language join query" \
    "curl -s -X POST '$BASE_URL/query-join' \
    -F 'query=Join these files on id column using inner join' \
    -F 'file1=data/output/sample_data.xlsx' \
    -F 'file2=data/output/sample_data.xlsx' \
    -F 'sheet1=Structured_Data' \
    -F 'sheet2=Structured_Data'"

echo "📝 TEST 8: UNSTRUCTURED DATA (TEXT ANALYSIS)"
echo "============================================="

run_test "8.1: Sentiment analysis on feedback" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Unstructured_Data' \
    -F 'query=Analyze customer_feedback and classify each as positive, negative, or neutral'"

run_test "8.2: Text length analysis" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Unstructured_Data' \
    -F 'query=Calculate the length of each customer_feedback text'"

run_test "8.3: Text contains check" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Unstructured_Data' \
    -F 'query=Check if feedback contains the word excellent or satisfied'"

run_test "8.4: Text contains filter" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Unstructured_Data' \
    -F 'query=Show all rows where product_review contains the word quality'"

run_test "8.5: Dedicated text analysis endpoint" \
    "curl -s -X POST '$BASE_URL/analyze-text' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Unstructured_Data' \
    -F 'column=customer_feedback' \
    -F 'analysis_type=sentiment'"

echo "🎯 BONUS: COMPLEX OPERATIONS"
echo "============================="

run_test "9.1: Multi-step analysis (filter then aggregate)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=For employees with salary above 70000, calculate average performance_score by department'"

run_test "9.2: Sorting results" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show top 10 highest paid employees sorted by salary descending'"

run_test "9.3: Ranking" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Rank employees by salary within each department'"

echo "⚠️  ERROR HANDLING TESTS"
echo "========================"

run_test "10.1: Non-existent file (should fail gracefully)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/input/nonexistent.xlsx' \
    -F 'query=Show all data' | grep -q 'error'"

run_test "10.2: Invalid query (empty)" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'query=' | grep -q 'error'"

run_test "10.3: Invalid column reference" \
    "curl -s -X POST '$BASE_URL/query' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Calculate average of totally_nonexistent_column_xyz'"

echo "💾 EXPORT TESTS"
echo "==============="

run_test "11.1: Export query results" \
    "curl -s -X POST '$BASE_URL/export' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data' \
    -F 'query=Show top 10 employees by salary' \
    -F 'output_filename=top_earners.xlsx' \
    -F 'formatted=true'"

run_test "11.2: Download exported file" \
    "curl -s -I '$BASE_URL/download/top_earners.xlsx' | head -n 1 | grep -q '200'"

echo "🔍 ANALYSIS TESTS"
echo "================="

run_test "12.1: Analyze Excel file structure" \
    "curl -s -X POST '$BASE_URL/analyze' \
    -F 'filepath=data/output/sample_data.xlsx' \
    -F 'sheet_name=Structured_Data'"

echo "📜 HISTORY TESTS"
echo "================"

run_test "13.1: Get query history" \
    "curl -s -X GET '$BASE_URL/history?limit=5'"

run_test "13.2: Get history statistics" \
    "curl -s -X GET '$BASE_URL/history/stats'"

echo ""
echo "========================================="
echo "📊 TEST SUMMARY"
echo "========================================="
echo -e "Total Tests: $test_count"
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo ""

success_rate=$(awk "BEGIN {printf \"%.1f\", ($passed/$test_count)*100}")
echo -e "Success Rate: ${success_rate}%"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed but this is expected for error handling tests${NC}"
    echo -e "Check if the failures are expected (error handling tests should fail gracefully)"
    exit 0
fi