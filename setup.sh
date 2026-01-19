#!/bin/bash

# =============================================================================
# CALORIE VISION TRACKER - SETUP SCRIPT
# =============================================================================

echo "🍎 Calorie Vision Tracker - Setup Script"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1)
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi
echo "✅ Found $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi
echo "✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi
echo "✅ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

# Check for secrets file
echo ""
if [ -f ".streamlit/secrets.toml" ]; then
    echo "✅ Secrets file found"
else
    echo "⚠️  No secrets file found at .streamlit/secrets.toml"
    echo "   Creating from template..."
    mkdir -p .streamlit
    cp secrets.template.toml .streamlit/secrets.toml
    echo ""
    echo "📝 Please edit .streamlit/secrets.toml with your API keys:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - SENDGRID_API_KEY (optional)"
    echo "   - SENDGRID_FROM_EMAIL (optional)"
fi

echo ""
echo "========================================="
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure your API keys in .streamlit/secrets.toml"
echo "2. Run the database schema in Supabase SQL Editor"
echo "3. Create 'food-images' storage bucket in Supabase"
echo "4. Start the app: streamlit run app.py"
echo ""
echo "For detailed instructions, see README.md"
echo "========================================="
