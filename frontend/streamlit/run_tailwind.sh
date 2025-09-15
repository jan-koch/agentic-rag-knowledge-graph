#!/bin/bash

# Run the Tailwind-based Streamlit app
echo "Starting Riddly Chat with Tailwind CSS..."
echo "----------------------------------------"
echo "Features:"
echo "✅ Tailwind CSS utility classes"
echo "✅ Simplified, clean layout"
echo "✅ Built-in dark mode support"
echo "✅ Responsive design"
echo "✅ Minimal custom CSS"
echo "✅ Modern animations"
echo "✅ ChatGPT-style interface"
echo "----------------------------------------"
echo ""

# Activate virtual environment if it exists
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
elif [ -d "../../venv_linux" ]; then
    source ../../venv_linux/bin/activate
fi

# Run the Tailwind app
streamlit run app_tailwind.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base "light"