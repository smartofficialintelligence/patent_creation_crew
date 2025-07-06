#!/bin/bash
# Installation script for Patent Automation System dependencies

echo "🔧 Installing Patent Automation System Dependencies"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $python_version"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
echo "📦 Installing core dependencies..."
pip install -r requirements.txt

# Verify critical dependencies
echo "🔍 Verifying critical dependencies..."
python3 -c "import psutil; print('✅ psutil installed successfully')"
python3 -c "import crewai; print('✅ crewai installed successfully')"
python3 -c "import openai; print('✅ openai installed successfully')"
python3 -c "import langchain; print('✅ langchain installed successfully')"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Set up your environment variables:"
echo "   export OPENAI_API_KEY='your-openai-api-key'"
echo "   export LANGCHAIN_API_KEY='your-langsmith-key'  # Optional"
echo "   export LENS_API_KEY='your-lens-key'  # Optional"
echo "   export EPO_API_KEY='your-epo-key'  # Optional"
echo ""
echo "2. Test the installation:"
echo "   python run_patent_automation.py --help"
echo ""
echo "3. Check system status:"
echo "   python scripts/monitor_status.py"
echo ""
echo "4. Run a test:"
echo "   python run_patent_automation.py --test" 