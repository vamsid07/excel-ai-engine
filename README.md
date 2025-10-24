# Excel AI Engine

AI-powered Excel data analysis and manipulation engine using Large Language Models.

## 🚀 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Comprehensive Operations**: Math, aggregations, filtering, pivoting, date operations, and joins
- **Synthetic Data Generation**: Built-in data generator for testing
- **REST API**: Clean and documented API endpoints
- **Docker Support**: Fully containerized application
- **Interactive Documentation**: Auto-generated Swagger UI

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

### 1. Generate Sample Data
```bash
POST /api/v1/generate-sample-data?rows=1000&include_unstructured=true
```

### 2. Upload Excel File
```bash
POST /api/v1/upload
Content-Type: multipart/form-data
Body: file (Excel file)
```

### 3. Query Excel Data
```bash
POST /api/v1/query
Content-Type: multipart/form-data
Body: 
  - filepath: "data/input/sample_data.xlsx"
  - query: "Calculate average salary by department"
```

### 4. List Supported Operations
```bash
GET /api/v1/operations
```

## 📖 Usage Examples

### Example 1: Generate and Query Data

```bash
# 1. Generate sample data
curl -X POST "http://localhost:8000/api/v1/generate-sample-data"

# 2. Query the data
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/output/sample_data.xlsx" \
  -F "query=Calculate average salary by department"
```

### Example 2: Upload Your Own Excel

```bash
# Upload your Excel file
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@/path/to/your/data.xlsx"

# Query it
curl -X POST "http://localhost:8000/api/v1/query" \
  -F "filepath=data/input/your_file.xlsx" \
  -F "query=Show me all rows where revenue > 10000"
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

### Day 2 Progress
- ✅ LLM service for intelligent query interpretation
- ✅ Excel service with safe code execution
- ✅ Complete query endpoint implementation
- ✅ Comprehensive error handling
- ✅ Unit tests (pytest)
- ✅ Testing guide with examples

### Upcoming (Day 3+)
- 🔄 Advanced operations (joins, complex pivots)
- 🔄 Unstructured data analysis (optional)
- 🔄 Performance optimizations

## 🤝 Contributing

This is a recruitment project. Code commits will be pushed daily.

## 📝 License

This project is for recruitment evaluation purposes.

## 📧 Contact

For questions or clarifications, contact the recruitment team.