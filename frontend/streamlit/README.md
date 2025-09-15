# 🤖 Agentic RAG Streamlit Chat (Deutsche Oberfläche)

Eine moderne Streamlit-Chat-Anwendung mit deutscher Benutzeroberfläche für das Agentic RAG System.

## ✨ Funktionen

### 🎨 Modernes Design
- **Elegante Oberfläche**: Gradient-Design mit professionellem Look
- **Responsive Layout**: Funktioniert auf Desktop und Tablet
- **Dark Mode Support**: Automatische Anpassung an System-Theme
- **Deutsche Lokalisierung**: Vollständig deutsche Benutzeroberfläche

### 💬 Chat-Funktionen
- **Echtzeit-Streaming**: Live-Antworten vom KI-Assistenten
- **Mehrere Suchtypen**: Hybrid, Vektor und Wissensgraph-Suche
- **Chat-Verlauf**: Persistente Konversationen pro Session
- **Tool-Tracking**: Anzeige verwendeter KI-Tools
- **Export-Funktion**: Chat-Verlauf als JSON exportieren

### ⚙️ Konfiguration
- **API-Einstellungen**: Flexible Server-Konfiguration
- **Authentifizierung**: Sichere API-Key Verwaltung
- **Verbindungstest**: Sofortige Validierung der Einstellungen
- **Benutzerfreundlich**: Intuitive Sidebar-Kontrollen

## 🚀 Installation & Start

### 1. Abhängigkeiten installieren

```bash
cd frontend/streamlit
pip install -r requirements.txt
```

### 2. API Server starten

Stellen Sie sicher, dass Ihr Agentic RAG API Server läuft:

```bash
# Im Hauptverzeichnis des Projekts
python -m agent.api
```

### 3. Streamlit App starten

```bash
streamlit run app.py
```

Die App öffnet sich automatisch in Ihrem Browser unter `http://127.0.0.1:8501`.

## 🎯 Verwendung

### Erste Schritte

1. **API-Konfiguration**:
   - Gehen Sie zur Sidebar (⚙️ Einstellungen)
   - Geben Sie die API Server URL ein (Standard: `http://localhost:8058`)
   - Fügen Sie Ihren API-Schlüssel hinzu

2. **Verbindung testen**:
   - Klicken Sie auf "🔄 Verbindung testen"
   - Warten Sie auf die Bestätigung "✅ Verbunden"

3. **Chat beginnen**:
   - Wählen Sie Ihren bevorzugten Suchtyp
   - Aktivieren Sie Streaming für Live-Antworten
   - Stellen Sie Ihre erste Frage!

### Suchtypen

- **🔀 Hybrid (Empfohlen)**: Kombiniert Vektor- und Wissensgraph-Suche
- **📊 Vektor-Suche**: Semantische Ähnlichkeitssuche
- **🕸️ Wissensgraph**: Beziehungsbasierte Suche

### Features

#### Streaming-Antworten
- Aktivieren Sie "⚡ Streaming" für Live-Antworten
- Sehen Sie den Assistenten in Echtzeit tippen
- Sofortige Reaktionen ohne Wartezeit

#### Chat-Management
- **🗑️ Chat leeren**: Neue Konversation beginnen
- **📥 Chat exportieren**: Verlauf als JSON-Datei herunterladen
- **Automatischer Verlauf**: Nachrichten werden pro Session gespeichert

#### Tool-Anzeige
- Sehen Sie welche KI-Tools verwendet wurden
- Farbcodierte Tool-Badges unter Antworten
- Transparenz über den Suchprozess

## 🎨 Anpassungen

### Design anpassen

Die App verwendet CSS Custom Properties für einfache Anpassungen:

```python
# In app.py, CSS-Sektion ändern
:root {
    --primary-color: #667eea;      # Hauptfarbe
    --secondary-color: #764ba2;    # Sekundärfarbe
    --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Texte ändern

Alle deutschen Texte sind in der `TEXTS` Dictionary definiert:

```python
TEXTS = {
    "title": "🤖 Ihr Custom Titel",
    "welcome_text": "Ihr angepasster Willkommenstext",
    # ...weitere Texte
}
```

### Features erweitern

Die modulare Struktur ermöglicht einfache Erweiterungen:

- `send_message()`: Für normale API-Aufrufe
- `send_streaming_message()`: Für Streaming-Funktionen
- `render_message()`: Für Nachrichten-Layout
- `test_api_connection()`: Für Verbindungstests

## 📱 Mobile Optimierung

Die App ist responsive gestaltet:

- **Tablet-freundlich**: Optimiert für 768px+ Bildschirme
- **Touch-optimiert**: Große Schaltflächen und Eingabefelder
- **Sidebar-Anpassung**: Streamlit's native responsive Sidebar

## 🔧 Fehlerbehebung

### Häufige Probleme

**Verbindungsfehler**:
```
❌ Verbindungsfehler: Connection refused
```
- Prüfen Sie, ob der API Server läuft (`python -m agent.api`)
- Überprüfen Sie die URL (Standard: `http://localhost:8058`)

**Authentifizierungsfehler**:
```
HTTP 401: Unauthorized
```
- Überprüfen Sie Ihren API-Schlüssel in der Sidebar
- Stellen Sie sicher, dass `API_KEY_REQUIRED=true` in Ihrer `.env` gesetzt ist

**Streaming-Probleme**:
```
Streaming-Fehler: ...
```
- Deaktivieren Sie Streaming temporär
- Prüfen Sie die Netzwerkverbindung
- Aktualisieren Sie die Seite (F5)

### Debug-Modus

Aktivieren Sie Streamlit's Debug-Modus:

```bash
streamlit run app.py --logger.level=debug
```

## 📊 Performance-Tipps

### Optimale Einstellungen
- **Streaming aktivieren**: Für bessere UX
- **Session Reuse**: Lassen Sie Session-ID automatisch verwalten
- **Kurze Nachrichten**: Für schnellere Antworten

### Ressourcen-Management
- Chat regelmäßig leeren bei langen Gesprächen
- API-Verbindung bei Fehlern neu testen
- Browser-Cache bei Problemen leeren

## 🛡 Sicherheit

### Best Practices
- **API-Keys**: Nie in Code einbetten, nur über Sidebar eingeben
- **HTTPS**: In Produktion nur verschlüsselte Verbindungen
- **CORS**: API Server entsprechend konfigurieren
- **Rate Limiting**: Bei öffentlichem Zugang implementieren

## 🌐 Deployment

### Lokale Entwicklung
```bash
streamlit run app.py
```

### Cloud Deployment (Streamlit Cloud)
1. Code zu GitHub Repository pushen
2. Mit Streamlit Cloud verbinden
3. Secrets für API-Konfiguration setzen
4. App deployen

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📚 Integration mit anderen Frontends

Diese Streamlit-App kann parallel zu anderen Frontend-Lösungen laufen:

- **Widget**: Für Website-Embedding
- **Standalone App**: Für vollständige Web-App
- **Streamlit**: Für interne Tools und Demos

Alle nutzen dieselbe API und sind kompatibel.

## 🆘 Support

Bei Problemen oder Fragen:

1. **Logs prüfen**: Streamlit zeigt Fehler im Browser/Terminal
2. **API testen**: Direkte API-Aufrufe mit curl/Postman
3. **Dokumentation**: Hauptprojekt README und API-Docs
4. **Issues**: GitHub Issues für Bugmeldungen

## 🔄 Updates

Die App wird automatisch mit neuen Streamlit-Funktionen kompatibel gehalten:

- **Session State**: Moderne Streamlit State Management
- **Widgets**: Aktuelle Streamlit Komponenten
- **Styling**: CSS3 und moderne Browser-Features
- **API**: Kompatibel mit aktueller Agentic RAG API