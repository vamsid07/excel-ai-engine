# Excel AI Engine

## Executive Summary

The Excel AI Engine is a production-grade intelligent data analysis platform that bridges the gap between natural language queries and complex data operations. Built with enterprise-level architecture and comprehensive security measures, this system transforms Excel data analysis from a manual, code-dependent process into an intuitive, conversational experience.

### Key Differentiators

**Intelligent Code Generation with Safety Guarantees**  
Unlike traditional data analysis tools, this engine dynamically generates pandas code from natural language while enforcing strict security boundaries. Every generated code block undergoes multi-layer validation to prevent file system access, network operations, and dangerous imports. The system maintains a whitelist of safe operations and rejects any code containing forbidden keywords such as `eval`, `exec`, `open`, `subprocess`, or unauthorized imports.

**Production-Ready Architecture**  
The application follows enterprise software design principles with a clear separation of concerns across API, service, and utility layers. Asynchronous request handling ensures scalability, while comprehensive error handling with detailed logging provides operational visibility. Query history tracking enables audit trails and performance monitoring.

**Comprehensive Test Coverage**  
With over 95% code coverage across 250+ unit tests and 38 integration tests, every component has been validated for reliability. The test suite covers normal operation paths, edge cases, error conditions, and security scenarios, ensuring consistent behavior in production environments.

**Full Operational Spectrum**  
The engine supports the complete range of data operations required for professional analytics: mathematical computations, statistical aggregations, multi-condition filtering, temporal analysis, pivot transformations, multi-file joins, and text sentiment analysis. Each operation type has been thoroughly tested and optimized for performance.

### Technical Excellence

**Robust Error Handling**  
The system implements defensive programming practices throughout. Invalid inputs are caught at the API layer with descriptive error messages. Generated code is validated before execution. Runtime errors are gracefully handled and returned with context. File operations respect size limits and format restrictions.

**Security-First Design**  
Code execution occurs in isolated namespaces with restricted access to system resources. The validation layer prevents injection attacks, unauthorized file access, and resource exhaustion. All user inputs are sanitized and validated before processing.

**Developer Experience**  
Interactive API documentation via Swagger UI allows immediate testing without external tools. Docker containerization ensures consistent deployment across environments. Environment-based configuration supports different deployment scenarios. Comprehensive logging aids debugging and monitoring.

**Performance Optimization**  
Results are automatically truncated to prevent memory issues with large datasets. Vectorized pandas operations ensure efficient processing. Query caching through history reduces redundant computations. Asynchronous processing prevents blocking operations.

## Core Features

### Natural Language Interface
Query your Excel data using plain English. The system interprets your intent and generates appropriate pandas code for execution.

### Comprehensive Data Operations
- Mathematical computations across columns
- Statistical aggregations with grouping
- Advanced filtering with multiple conditions
- Date manipulation and temporal analysis
- Pivot table creation and reversal
- Multi-file joining capabilities
- Text analysis and sentiment classification

### Production-Ready Architecture
- RESTful API with FastAPI
- Robust error handling and validation
- Query history tracking
- Result export with formatting
- Batch query processing
- Docker containerization
- Interactive API documentation (Swagger UI)
- Comprehensive unit test coverage (95%+)

## Prerequisites

- Python 3.11 or higher
- Docker Desktop (optional)
- Ollama with llama3.2 model installed

## Ollama Setup

Install Ollama and pull the required model:

```bash
curl -fsSL https://ollama.com/install.sh | sh

ollama pull llama3.2

ollama serve
```

## Installation

### Local Development

```bash
git clone <repository-url>
cd excel-ai-engine

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
```

Edit `.env` and configure Ollama settings:
```
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Start the server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access the API at `http://localhost:8000`

### Docker Deployment

Ensure Ollama is running on your host machine, then:

```bash
docker-compose up --build -d
```

The service will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Quick Start

### 1. Generate Test Data

```bash
curl -X POST "http://localhost:8000/api/v1/generate-sample-data?rows=1000&include_unstructured=true"
```

This creates a sample Excel file with 1000 rows of structured and unstructured data.

### 2. Run Queries

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "sheet_name=Structured_Data" \
  -F "query=Calculate average salary by department"
```

### 3. Run Complete Test Suite

```bash
chmod +x testing.sh
./testing.sh
```

## Supported Query Types

### Mathematical Operations
Create calculated columns by combining existing data with arithmetic operations.

**Examples:**
- "Create a new column monthly_salary by dividing salary by 12"
- "Add salary and bonus to create total_compensation column"
- "Multiply performance_score by 1000 to get performance_bonus"

### Aggregation Analysis
Perform statistical computations with optional grouping.

**Examples:**
- "Calculate average salary by department"
- "Show sum, average, minimum and maximum salary by department"
- "Count how many employees are in each city"
- "Calculate standard deviation of salary by department"

### Data Filtering
Extract subsets based on single or multiple conditions.

**Examples:**
- "Show employees with salary greater than 100000"
- "Filter employees with age greater than 40 AND salary greater than 80000"
- "Show employees in Engineering department OR with salary above 120000"
- "Find all employees whose city name contains New"

### Temporal Operations
Extract date components or calculate time differences.

**Examples:**
- "Extract the year from join_date column and create a new column called join_year"
- "Extract month and day from join_date"
- "Calculate years of service from join_date to today"
- "Show employees who joined after 2020"

### Pivot Tables
Transform data between wide and long formats.

**Examples:**
- "Create a pivot table with department as rows and average salary"
- "Create pivot table with department as rows, city as columns, and average salary as values"
- "Pivot table showing total projects_completed by department"

### Unpivot Operations
Convert wide format to long format.

**Examples:**
- "Unpivot the data keeping id and name as identifiers and converting salary, age, projects_completed into separate rows"

### Data Joining
Combine multiple datasets based on common keys.

**Examples:**
- "Join these files on id column using inner join"
- Direct API call with file paths and join parameters

### Text Analysis
Classify or analyze unstructured text content.

**Examples:**
- "Analyze customer_feedback and classify each as positive, negative, or neutral"
- "Calculate the length of each customer_feedback text"
- "Show all rows where product_review contains the word quality"

## API Endpoints

### Core Operations
- `POST /api/v1/generate-sample-data` - Generate synthetic test data
- `POST /api/v1/upload` - Upload Excel file
- `POST /api/v1/query` - Execute natural language query
- `POST /api/v1/analyze` - Get detailed file analysis
- `GET /api/v1/sheets/{filepath}` - List available sheets

### Advanced Operations
- `POST /api/v1/join` - Join two files
- `POST /api/v1/query-join` - Natural language join query
- `POST /api/v1/export` - Execute query and export
- `GET /api/v1/download/{filename}` - Download exported file
- `POST /api/v1/analyze-text` - Text analysis operations

### History Management
- `GET /api/v1/history` - View query history
- `GET /api/v1/history/stats` - Get usage statistics

### System
- `GET /api/v1/health` - Service health check

## Testing

### Run Unit Tests

The project includes comprehensive unit tests with 95%+ code coverage.

```bash
pytest
```

### Run Tests with Coverage Report

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### View Coverage Report

```bash
open htmlcov/index.html
```

### Run Specific Tests

```bash
pytest tests/test_excel_service.py
pytest tests/test_llm_service.py
pytest tests/test_routes.py
```

### Run Integration Tests

Run the complete test suite covering all 8 required operations:

```bash
chmod +x testing.sh
./testing.sh
```

The test suite validates:
1. Basic Math Operations (3 tests)
2. Aggregation Operations (4 tests)
3. Filter Operations (4 tests)
4. Date Operations (4 tests)
5. Pivot Operations (3 tests)
6. Unpivot Operations (1 test)
7. Join Operations (3 tests)
8. Unstructured Data Operations (5 tests)
9. Complex Operations (3 tests)
10. Error Handling (3 tests)
11. Export Operations (2 tests)
12. Analysis Operations (1 test)
13. History Operations (2 tests)

**Total: 38 integration tests + 250+ unit tests**


## Configuration

Environment variables can be set in `.env`:

```
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=.xlsx,.xls
```

## Architecture

The system follows a layered architecture:

1. **API Layer** (routes.py) - HTTP request/response handling
2. **Service Layer** - Business logic
   - LLM Service - Code generation and validation
   - Excel Service - File reading and code execution
   - Join Service - Multi-file operations
   - Export Service - Result formatting and export
   - Text Service - Unstructured data analysis
   - Query History - Tracking and statistics
3. **Utility Layer** - Helper functions and data generation
4. **Test Layer** - Comprehensive unit and integration tests

## How It Works

1. User submits natural language query via API
2. System reads Excel file and extracts metadata
3. LLM generates pandas code based on query and data structure
4. Code is validated for security and correctness
5. Code executes in isolated namespace
6. Results are formatted and returned to user
7. Query and result are logged to history

## Security Considerations

The system includes multiple safety measures:
- Code validation before execution
- Restricted import statements
- No file system access from generated code
- No network operations from generated code
- Input sanitization and validation
- File size limits (50MB max)

## Performance

- Maximum file size: 50MB
- Result truncation: 10,000 rows
- Query timeout: 120 seconds
- Concurrent request handling via async operations

## Error Handling

The API provides detailed error responses with:
- HTTP status codes
- Error type classification
- Descriptive error messages
- Timestamps for debugging

## Project Structure

```
excel-ai-engine/
├── app/
│   ├── api/
│   │   └── routes.py
│   ├── core/
│   │   └── config.py
│   ├── services/
│   │   ├── excel_service.py
│   │   ├── llm_service.py
│   │   ├── join_service.py
│   │   ├── export_service.py
│   │   ├── text_service.py
│   │   └── query_history.py
│   ├── utils/
│   │   └── data_generator.py
│   └── main.py
├── data/
│   ├── input/
│   └── output/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_data_generator.py
│   ├── test_excel_service.py
│   ├── test_export_service.py
│   ├── test_join_service.py
│   ├── test_llm_service.py
│   ├── test_query_history.py
│   ├── test_routes.py
│   └── test_text_service.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── testing.sh
└── README.md
```


## License

MIT License

## Support

For issues or questions, please open an issue on the repository.