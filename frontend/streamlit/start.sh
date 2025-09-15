#!/bin/bash
# Sicherer Start-Skript für Streamlit App
# Stellt sicher, dass nur auf localhost gehört wird

echo "🧩 Starte Riddly Chat Agent (Streamlit)..."
echo "🔒 Konfiguriert für localhost-only (127.0.0.1:8501)"
echo

# Prüfe ob Riddly API Server läuft
if curl -s -H "Authorization: Bearer J_qfzc5WsTZ5GgyyOhFGplfI7zoDSFrY0XqTitDadmE" https://riddly.kobra-dataworks.de/health > /dev/null 2>&1; then
    echo "✅ Riddly API Server ist erreichbar"
else
    echo "❌ Riddly API Server nicht erreichbar (riddly.kobra-dataworks.de)"
    echo "🌐 Überprüfen Sie Internetverbindung und Server-Status"
    echo
fi

# Starte Streamlit mit expliziten Sicherheits-Einstellungen
streamlit run app.py \
    --server.address 127.0.0.1 \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    --theme.base light