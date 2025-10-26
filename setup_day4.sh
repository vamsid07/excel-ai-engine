#!/bin/bash

echo "🎨 Setting up Day 4 - Web Interface"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Please run this from the excel-ai-engine directory"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run Day 1 setup first."
    exit 1
fi

echo "📁 Creating static directory..."
mkdir -p app/static

echo ""
echo "✅ Day 4 setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Make sure app/static/index.html is created (copy from artifact)"
echo "2. Update app/main.py (copy from artifact)"
echo "3. Start server: python -m app.main"
echo "4. Open browser: http://localhost:8000"
echo ""
echo "📚 Documentation:"
echo "- Day 4 Testing: docs/DAY4_TESTING.md"
echo "- Main README: README.md"
echo ""
echo "🌐 Web UI will be available at: http://localhost:8000"
echo "📖 API Docs will be at: http://localhost:8000/api/docs"
echo ""