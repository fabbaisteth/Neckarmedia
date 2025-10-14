# Neckarmedia Chatbot

Ein AI-gestützter Chatbot für Neckarmedia, der Kunden auf Ihrer Website über das Unternehmen informiert.

## ✨ Features

- 🚀 **Öffentlich zugänglich** - Keine Anmeldung erforderlich
- 🔒 **Sicher** - Rate Limiting, Input Validation, CORS Protection
- 🎯 **Einfach zu deployen** - Docker-ready, cloud-ready
- 💬 **Intelligente Antworten** - RAG-basiert mit Firmenwissen
- 🌐 **Website-Integration** - Einfach einbettbar in jede Website

## 🚀 Quick Start

**Lokales Testen in 2 Minuten:**

```bash
# 1. Umgebungsvariablen setzen
cp .env.example .env
# Editiere .env und füge deinen OPENAI_API_KEY ein

# 2. Mit Docker starten
docker-compose up -d

# 3. Testen
curl http://localhost:8000/health
```

**Vollständige Anleitung:** Siehe [QUICK_START.md](QUICK_START.md)

## 📚 Dokumentation

- **[QUICK_START.md](QUICK_START.md)** - In 5 Minuten loslegen
- **[PUBLIC_DEPLOYMENT.md](PUBLIC_DEPLOYMENT.md)** - Vollständiger Deployment-Guide für öffentliche Website
- **[API_README.md](API_README.md)** - API Dokumentation

## 🏗️ Architektur

- **Backend:** FastAPI REST API
- **Frontend:** Optional Gradio UI (für Entwicklung)
- **RAG System:** Langchain + ChromaDB mit Firmenwissen
- **Datenbank:** SQLite für Embeddings
- **Deployment:** Docker + Docker Compose

## 📝 Beispiel-Fragen

- "Who founded Neckarmedia?"
- "Who is Karla?"
- "What is the workflow Neckarmedia has?"
- "What are the latest job offerings?"
- "Give two examples of Neckarmedia's references."

## 🔧 Entwicklung

```bash
# Virtuelle Umgebung aktivieren
source neckarvenv/bin/activate

# API starten
python api.py

# Gradio UI starten (optional)
python gradio_app.py
```

## Dependencies

1. Structure of neckarmedia career page html
2. Structure of the employee and founder doc (includes karla)
3. Latest run of the blog crawl (needs update when new blog is posted)