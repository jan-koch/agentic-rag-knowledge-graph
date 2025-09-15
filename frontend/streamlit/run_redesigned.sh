#!/bin/bash

# Run the redesigned Streamlit app
echo "Starting Redesigned Riddly Chat Interface..."
echo "----------------------------------------"
echo "Features:"
echo "✅ ChatGPT-like clean interface"
echo "✅ Light/Dark theme toggle"
echo "✅ Session management in sidebar"
echo "✅ Message bubbles with avatars"
echo "✅ Fixed header and input area"
echo "✅ Smooth animations"
echo "✅ Mobile responsive design"
echo "✅ Copy buttons and message actions"
echo "----------------------------------------"
echo ""

# Activate virtual environment if it exists
if [ -d "../../venv" ]; then
    source ../../venv/bin/activate
elif [ -d "../../venv_linux" ]; then
    source ../../venv_linux/bin/activate
fi

# Run the redesigned app
streamlit run app_redesigned.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base "light"