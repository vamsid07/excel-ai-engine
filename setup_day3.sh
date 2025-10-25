#!/bin/bash

echo "🚀 Setting up Day 3 - Excel AI Engine"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run Day 1 setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "📦 Installing new dependencies..."
pip install -r requirements.txt

echo ""
echo "📁 Creating necessary directories..."
mkdir -p data/input
mkdir -p data/output
mkdir -p docs

echo ""
echo "✅ Day 3 setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Make sure Ollama is running (or OpenAI API key is set)"
echo "2. Start the server: python -m app.main"
echo "3. Test endpoints: See docs/DAY3_TESTING.md"
echo "4. View API docs: http://localhost:8000/docs"
echo ""
echo "📚 Documentation:"
echo "- Day 3 Testing: docs/DAY3_TESTING.md"
echo "- Main README: README.md"
echo ""