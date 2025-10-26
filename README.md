# Excel AI Engine

AI-powered Excel data analysis and manipulation engine using Large Language Models.

## 🚀 Features

- **🌐 Interactive Web Interface** - Beautiful, modern UI for non-technical users
- **🤖 Natural Language Queries** - Ask questions about your data in plain English
- **📊 Real-time Results** - Instant query execution with visual feedback
- **🎨 Data Visualization** - Tables, charts, and statistics
- **💾 Export Functionality** - Download results as formatted Excel files
- **📜 Query History** - Track and replay previous queries
- **🔗 Multi-File Operations** - Join and merge multiple Excel files
- **⚡ Batch Processing** - Execute multiple queries in sequence
- **🎯 Smart Suggestions** - AI-powered query recommendations
- **📱 Responsive Design** - Works on desktop, tablet, and mobile
- **🚀 Production Ready** - Comprehensive error handling and validation

## 📋 Prerequisites

- Python 3.11+
- Docker Desktop (optional)
- OpenAI API Key

## 🛠️ Installation

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/excel-ai-engine.git
cd excel-ai-engine
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

5. **Run the application**
```bash
python -m app.main
```

The API will be available at: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Setup

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

2. **Access the API**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 📊 Generate Sample Data

Generate synthetic data for testing:

```bash
# Using Python directly
python -m app.utils.data_generator

# Using the API
curl -X POST "http://localhost:8000/api/v1/generate-sample-data?rows=1000&include_unstructured=true"
```

This creates a file at `data/output/sample_data.xlsx` with:
- **Structured_Data** sheet: 1000 rows × 10 columns (numerical and categorical data)
- **Unstructured_Data** sheet: 1000 rows × 5 columns (text data)

## 🔌 API Endpoints

### Core Operations
- `POST /api/v1/generate-sample-data` - Generate synthetic test data
- `POST /api/v1/upload` - Upload single Excel file
- `POST /api/v1/upload-multiple` - Upload multiple files
- `POST /api/v1/query` - Execute natural language query
- `POST /api/v1/analyze` - Get detailed data analysis
- `GET /api/v1/sheets/{filepath}` - List sheets in file

### Join Operations (New in Day 3)
- `POST /api/v1/join` - Join two Excel files
- `POST /api/v1/query-with-join` - Join and query in one operation
- `POST /api/v1/analyze-join` - Analyze join potential

### Export Operations (New in Day 3)
- `POST /api/v1/export` - Execute query and export result
- `GET /api/v1/download/{filename}` - Download exported file
- `GET /api/v1/exports` - List all exported files

### Batch Processing (New in Day 3)
- `POST /api/v1/batch-query` - Execute multiple queries

### Query History (New in Day 3)
- `GET /api/v1/history` - Get recent queries
- `GET /api/v1/history/{id}` - Get specific query
- `GET /api/v1/history/search/{term}` - Search history
- `GET /api/v1/history/stats` - Get statistics
- `DELETE /api/v1/history` - Clear history

### System
- `GET /api/v1/operations` - List supported operations
- `GET /api/v1/health` - Health check

## 📖 Usage Examples

### Example 1: Simple Query

```bash
# Generate data
curl -X POST "http://localhost:8000/api/v1/generate-sample-data"

# Query it
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary by department"
```

### Example 2: Join Multiple Files

```bash
# Upload files
curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@employees.xlsx"
curl -X POST "http://localhost:8000/api/v1/upload" -F "file=@departments.xlsx"

# Join and query
curl -X POST "http://localhost:8000/api/v1/query-with-join" \
  -F "file1=data/input/employees.xlsx" \
  -F "file2=data/input/departments.xlsx" \
  -F "query=Show average salary by department with budget information" \
  -F "join_columns=department"
```

### Example 3: Batch Processing

```bash
curl -X POST "http://localhost:8000/api/v1/batch-query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F 'queries=["Filter salary > 80000", "Group by department", "Sort by average descending"]' \
  -F "chain=true"
```

### Example 4: Export Results

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Show top 10 highest paid employees" \
  -F "output_filename=high_earners.xlsx" \
  -F "formatted=true"

# Download
open http://localhost:8000/api/v1/download/high_earners.xlsx
```

### Example 5: Query History

```bash
# View recent queries
curl "http://localhost:8000/api/v1/history?limit=10"

# Get statistics
curl "http://localhost:8000/api/v1/history/stats"

# Search history
curl "http://localhost:8000/api/v1/history/search/salary"
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_api.py -v
```

## 📁 Project Structure

```
excel-ai-engine/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration settings
│   ├── services/
│   │   ├── __init__.py
│   │   ├── excel_service.py    # Excel processing logic
│   │   └── llm_service.py      # LLM integration
│   ├── utils/
│   │   ├── __init__.py
│   │   └── data_generator.py   # Synthetic data generation
│   └── tests/
│       ├── __init__.py
│       └── test_api.py         # API tests
├── data/
│   ├── input/                  # Uploaded Excel files
│   └── output/                 # Generated/processed files
├── docs/                       # Additional documentation
├── .env                        # Environment variables
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🎯 Supported Operations

### Basic Math Operations
- Addition, subtraction, multiplication, division
- Example: "Add salary and bonus columns"

### Aggregations
- Sum, average, min, max, count, median
- Example: "Calculate average salary by department"

### Filtering
- Conditional filtering on any column
- Example: "Show rows where age > 30 and department is Engineering"

### Date Operations
- Extract year, month, day
- Calculate date differences
- Example: "Extract year from join_date"

### Joining
- Inner, left, right, outer joins
- Example: "Join with sales_data on customer_id"

### Pivot & Unpivot
- Create pivot tables
- Reverse pivot operations
- Example: "Create pivot table with department as rows and average salary"

## 🔧 Development

### Day 1 Progress
- ✅ Project structure setup
- ✅ Basic API endpoints
- ✅ Data generation utility
- ✅ Docker configuration
- ✅ Documentation

### Day 3 Progress ✅
- ✅ Join service for multi-file operations
- ✅ Export service with formatted Excel output
- ✅ Query history with search and statistics
- ✅ Batch processing (independent and chained)
- ✅ File download endpoints
- ✅ Enhanced error handling
- ✅ Comprehensive testing guide

### Optional Enhancements (Day 4+)
- 🔄 Web UI for non-technical users
- 🔄 Data visualization/charts
- 🔄 Advanced caching and performance optimization
- 🔄 Unstructured data analysis (sentiment, summarization)

## 🤝 Contributing

This is a recruitment project. Code commits will be pushed daily.

## 📝 License

This project is for recruitment evaluation purposes.

## 📧 Contact

For questions or clarifications, contact the recruitment team.