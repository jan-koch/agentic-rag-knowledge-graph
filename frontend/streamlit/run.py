#!/usr/bin/env python3
"""
Starter script für die Streamlit Chat App.
Prüft Abhängigkeiten und startet die Anwendung.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_dependencies():
    """Überprüft, ob alle erforderlichen Pakete installiert sind."""
    try:
        import importlib.util
        if importlib.util.find_spec("streamlit") is None or importlib.util.find_spec("requests") is None:
            raise ImportError("streamlit or requests not found")
        return True
    except ImportError as e:
        print(f"❌ Fehlende Abhängigkeit: {e}")
        print("📦 Installieren Sie die Abhängigkeiten mit: pip install -r requirements.txt")
        return False

def check_api_server():
    """Überprüft, ob der API Server erreichbar ist."""
    try:
        import requests
        headers = {
            "Authorization": "Bearer J_qfzc5WsTZ5GgyyOhFGplfI7zoDSFrY0XqTitDadmE"
        }
        response = requests.get("https://riddly.kobra-dataworks.de/health", headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Riddly API Server ist erreichbar")
            return True
        else:
            print(f"⚠️ Riddly API Server antwortet mit Status {response.status_code}")
            return False
    except Exception as e:
        print("❌ Riddly API Server ist nicht erreichbar")
        print(f"   Fehler: {str(e)}")
        print("🌐 Überprüfen Sie die Internetverbindung und Server-Status")
        return False

def main():
    """Hauptfunktion zum Starten der Streamlit App."""
    print("🎨 Starte Riddly Chat Agent mit Tailwind CSS...")
    print()
    
    # Arbeitsverzeichnis wechseln
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Abhängigkeiten prüfen
    print("📋 Prüfe Abhängigkeiten...")
    if not check_dependencies():
        sys.exit(1)
    
    # API Server prüfen
    print("🔍 Prüfe API Server...")
    api_available = check_api_server()
    if not api_available:
        print("⚠️ API Server nicht verfügbar - Sie können ihn in der App konfigurieren")
    
    print()
    print("✨ Neue Features:")
    print("  🎨 Tailwind CSS Design")
    print("  🌙 Dark/Light Mode Toggle")  
    print("  📱 Vollständig responsive")
    print("  💬 ChatGPT-ähnliche Oberfläche")
    print("  📚 Session-Verwaltung")
    print("  ⚡ Streaming-Antworten")
    print()
    print("📱 Verfügbare Anwendungen:")
    print("  💬 Riddly AI Chat: http://127.0.0.1:8501")
    if api_available:
        print("  🔗 Riddly API: https://riddly.kobra-dataworks.de/health")
    print("  🔒 Streamlit nur auf localhost (127.0.0.1) für Sicherheit")
    print("  🌐 Verbindet mit Riddly Server: riddly.kobra-dataworks.de")
    print()
    
    # Streamlit starten
    try:
        print("▶️ Starte Tailwind Streamlit App...")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address", "127.0.0.1",
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--theme.base", "light"
        ])
    except KeyboardInterrupt:
        print("\n👋 Streamlit App wurde beendet.")
    except Exception as e:
        print(f"❌ Fehler beim Starten der App: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()