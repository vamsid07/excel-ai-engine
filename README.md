# Excel AI Engine

An intelligent data analysis platform that enables natural language querying of Excel datasets using Large Language Models. The system automatically generates and executes pandas code to perform complex data operations on both structured and unstructured data.

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

## Prerequisites

- Python 3.11 or higher
- Docker Desktop (optional)
- Ollama with llama3.2 model installed

## Ollama Setup

Install Ollama and pull the required model:

```bash
# Install Ollama from https://ollama.ai

# Pull llama3.2 model
ollama pull llama3.2

# Start Ollama server
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
python -m app.main
```

Access the API at `http://localhost:8000`

### Docker Deployment

Ensure Ollama is running on your host machine, then:

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Generate Test Data

```bash
python -m app.utils.data_generator
```

This creates a sample Excel file with 1000 rows of structured data including employee information, dates, and performance metrics.

### Basic Query

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary by department"
```

### File Upload

```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@your_file.xlsx"
```

### Multi-File Join

```bash
curl -X POST "http://localhost:8000/api/v1/join" \
  -F "file1=data/input/employees.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "join_columns=department_id" \
  -F "how=inner"
```

### Export Results

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Show top 10 highest paid employees" \
  -F "output_filename=top_earners.xlsx" \
  -F "formatted=true"
```

## Supported Query Types

### Mathematical Operations
Create calculated columns by combining existing data with arithmetic operations.

Example: "Add salary and bonus to create total_compensation column"

### Aggregation Analysis
Perform statistical computations with optional grouping.

Example: "Show sum, average, minimum and maximum salary by department"

### Data Filtering
Extract subsets based on single or multiple conditions.

Example: "Find employees with age over 40 and salary above 80000"

### Temporal Operations
Extract date components or calculate time differences.

Example: "Calculate years of service from join_date to today"

### Pivot Tables
Transform data between wide and long formats.

Example: "Create pivot with department as rows and average salary by city"

### Data Joining
Combine multiple datasets based on common keys.

Example: "Join employee data with sales data on employee_id"

### Text Analysis
Classify or analyze unstructured text content.

Example: "Classify customer feedback as positive, negative, or neutral"

## Project Structure

```
excel-ai-engine/
├── app/
│   ├── api/
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   └── config.py           # Configuration
│   ├── services/
│   │   ├── excel_service.py    # Excel processing
│   │   ├── llm_service.py      # LLM integration
│   │   ├── join_service.py     # Multi-file operations
│   │   ├── export_service.py   # Result export
│   │   └── query_history.py    # History tracking
│   ├── utils/
│   │   └── data_generator.py   # Test data creation
│   └── main.py                 # Application entry
├── data/
│   ├── input/                  # Upload directory
│   └── output/                 # Results directory
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

### Core Operations
- `POST /api/v1/generate-sample-data` - Generate synthetic test data
- `POST /api/v1/upload` - Upload Excel file
- `POST /api/v1/query` - Execute natural language query
- `POST /api/v1/analyze` - Get detailed file analysis
- `GET /api/v1/sheets/{filepath}` - List available sheets

### Advanced Operations
- `POST /api/v1/join` - Join two files
- `POST /api/v1/export` - Execute query and export
- `GET /api/v1/download/{filename}` - Download exported file

### History Management
- `GET /api/v1/history` - View query history
- `GET /api/v1/history/stats` - Get usage statistics
- `GET /api/v1/history/search/{term}` - Search past queries

### System
- `GET /api/v1/health` - Service health check

## Testing

Run the complete test suite:

```bash
chmod +x testing.sh
./testing.sh
```

The script validates all supported operations including math, aggregations, filtering, dates, pivots, joins, and text analysis.

For unit tests:

```bash
pytest
pytest --cov=app --cov-report=html
```

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

## LLM Integration

The system uses Ollama for local LLM inference, providing:
- Complete data privacy (no external API calls)
- No usage costs
- Fast inference on local hardware
- Full control over model selection

### Supported Models
While the default is llama3.2, you can use other Ollama models by updating `OLLAMA_MODEL` in your `.env` file. Tested with:
- llama3.2 (recommended)
- llama3.1
- mistral
- codellama

## Security Considerations

The system includes multiple safety measures:
- Code validation before execution
- Restricted import statements
- No file system access from generated code
- No network operations from generated code
- Input sanitization and validation
- File size limits

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

## Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

### Docker Networking
If Docker container cannot connect to Ollama on host:
- Use `host.docker.internal:11434` (macOS/Windows)
- Use `172.17.0.1:11434` (Linux)
- Or add `network_mode: "host"` to docker-compose.yml

### Model Not Found
```bash
# Verify model is installed
ollama list

# Pull model if missing
ollama pull llama3.2
```

## Architecture

The system follows a layered architecture:

1. **API Layer** (routes.py) - Handles HTTP requests and responses
2. **Service Layer** - Business logic for different operations
   - LLM Service - Code generation and validation
   - Excel Service - File reading and code execution
   - Join Service - Multi-file operations
   - Export Service - Result formatting and export
3. **Utility Layer** - Helper functions and data generation

## How It Works

1. User submits natural language query via API
2. System reads Excel file and extracts metadata
3. LLM generates pandas code based on query and data structure
4. Code is validated for security and correctness
5. Code executes in isolated namespace
6. Results are formatted and returned to user
7. Query and result are logged to history

## Contributing

Contributions are welcome. Please ensure:
- Code follows existing style patterns
- All tests pass
- New features include appropriate tests
- Documentation is updated

## License

MIT License

## Support

For issues or questions, please open an issue on the repository.