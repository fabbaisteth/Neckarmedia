# Neckarmedia Chatbot Architecture & Setup Guide

This document provides a comprehensive overview of the Neckarmedia chatbot system, including script descriptions, file requirements, data formats, and the complete workflow for setting up embeddings and running the agent.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Script Descriptions](#script-descriptions)
3. [File Requirements](#file-requirements)
4. [Data Formats](#data-formats)
5. [Setup Workflow](#setup-workflow)
6. [Execution Flow](#execution-flow)

---

## 🎯 System Overview

The Neckarmedia chatbot is a RAG (Retrieval-Augmented Generation) system that answers questions about Neckarmedia using multiple data sources:

- **Blog articles** (crawled from the website)
- **Employee/Founder information** (from JSON files)
- **Service descriptions** (from structured JSON)
- **Job listings** (scraped live from the website)
- **Document knowledge** (from Google Drive documents)

The system uses:
- **SQLite database** (`neckarmedia.db`) for blog articles with vector embeddings
- **Sentence Transformers** (`all-MiniLM-L6-v2`) for semantic search
- **OpenAI GPT** for generating responses
- **FastAPI** for the REST API
- **Gradio** for the web UI (optional)

---

## 📜 Script Descriptions

### Core Scripts

#### `services/crawl_blog.py`
**Purpose:** Crawls blog posts from the Neckarmedia website and saves them to JSON.

**What it does:**
- Fetches blog archive links from `https://www.neckarmedia.com/news-blog/`
- Extracts individual blog post URLs from archive pages
- Crawls each blog post and extracts:
  - Title
  - Content (cleaned HTML)
  - Publication date
  - Source URL
- Saves all posts to `data/blog_posts.json`

**Output:** `data/blog_posts.json` (array of blog post objects)

**When to run:** When new blog posts are published on the website.

---

#### `services/db_sql.py`
**Purpose:** Initializes the SQLite database schema for blog articles.

**What it does:**
- Creates `neckarmedia.db` if it doesn't exist
- Creates `blog_articles` table with columns:
  - `id` (PRIMARY KEY)
  - `title` (TEXT)
  - `content` (TEXT)
  - `summary` (TEXT)
  - `keywords` (TEXT)
  - `source_url` (TEXT)
  - `date` (TEXT)
  - `embedding` (TEXT) - JSON-encoded vector embeddings

**Output:** Database file `neckarmedia.db` with schema

**When to run:** First-time setup or when schema changes are needed.

---

#### `services/insert_blog_db.py`
**Purpose:** Inserts blog articles from JSON into the database with AI-generated summaries and keywords.

**What it does:**
- Loads articles from `data/blog_posts.json`
- For each article:
  - Uses GPT-4 to generate a summary
  - Extracts standardized keywords from content
  - Extracts company names mentioned
  - Inserts or updates the article in the database
- Handles duplicates (updates summary/keywords if article exists)

**Dependencies:**
- Requires `OPENAI_API_KEY` in `.env`
- Reads from `data/services.json` for standardized keywords
- Requires `neckarmedia.db` to exist (run `db_sql.py` first)

**Output:** Populated `neckarmedia.db` with blog articles

**When to run:** After crawling new blog posts or when updating summaries/keywords.

---

#### `services/generate_embeddings_db.py`
**Purpose:** Generates and stores vector embeddings for blog articles in the database.

**What it does:**
- Loads all articles from `neckarmedia.db`
- Computes embeddings using `sentence-transformers/all-MiniLM-L6-v2`
- Stores embeddings as JSON strings in the `embedding` column
- Only processes articles that don't have embeddings yet

**Dependencies:**
- Requires `neckarmedia.db` with articles (run `insert_blog_db.py` first)
- Downloads the embedding model on first run (~80MB)

**Output:** Updated `neckarmedia.db` with embeddings for all articles

**When to run:** After inserting new articles or when regenerating embeddings.

---

#### `services/embeddings.py`
**Purpose:** Alternative script for generating embeddings (simpler version).

**What it does:**
- Similar to `generate_embeddings_db.py` but processes all articles regardless of existing embeddings
- Useful for regenerating all embeddings from scratch

**When to use:** When you need to regenerate all embeddings.

---

#### `services/handle_gdrive.py`
**Purpose:** Downloads documents from Google Drive, processes them, and stores them in ChromaDB.

**What it does:**
- Lists files from a Google Drive folder (configured via `FOLDER_ID`)
- Downloads PDF and DOCX files
- Extracts text from documents
- Splits text into chunks (1000 chars, 200 overlap)
- Annotates metadata (category, language, entities, keywords)
- Stores chunks in ChromaDB vector database

**Dependencies:**
- Requires `GOOGLE_DRIVE_API` key in `.env`
- Requires `FOLDER_ID` (hardcoded: `"1af9TUTNrBSkaoHZrSyqYWSTYqk0UiER3"`)
- Requires German spaCy model: `python -m spacy download de_core_news_md`
- Downloads Hugging Face models on first run

**Output:** `chroma_db/` directory with vector embeddings

**Note:** This script is currently not integrated into the main agent workflow but can be used for document-based retrieval.

**When to run:** When documents in Google Drive are updated.

---

#### `services/agent.py`
**Purpose:** Main agent script that handles user queries and generates responses.

**What it does:**
- Loads service descriptions from `data/services.json`
- Provides tools for:
  - **Founder/Employee Info**: Returns data from `data/latest_info.json`
  - **Company References (SQLite)**: Vector search in blog articles
  - **Jobs Scraper**: Live scraping from careers page
  - **Service Offerings**: Returns service descriptions
- Uses LLM to decide which tool to use based on user query
- Generates contextual responses using GPT

**Dependencies:**
- Requires `neckarmedia.db` with embeddings
- Requires `data/services.json`
- Requires `data/latest_info.json`
- Requires `OPENAI_API_KEY` in `.env`

**Output:** Chat responses (used by API)

**When to run:** Called automatically by the API when users send queries.

---

#### `services/keyword_list.py`
**Purpose:** Utility script to extract and display unique keywords from the database.

**What it does:**
- Queries all keywords from `blog_articles` table
- Normalizes and deduplicates keywords
- Prints sorted list of unique keywords

**When to run:** For analysis/debugging purposes.

---

### Application Scripts

#### `api.py`
**Purpose:** FastAPI REST API server for the chatbot.

**What it does:**
- Exposes `/chat_response` endpoint (POST)
- Implements rate limiting (per IP)
- CORS protection
- Input validation
- Security headers
- Calls `services/agent.py` to generate responses

**Configuration (via `.env`):**
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `RATE_LIMIT_REQUESTS`: Max requests per period (default: 20)
- `RATE_LIMIT_PERIOD`: Time window in seconds (default: 60)
- `ENVIRONMENT`: `development` or `production`
- `PUBLIC_MODE`: `true` or `false`

**When to run:** Continuously in production (via systemd or Docker).

---

#### `gradio_app.py`
**Purpose:** Web UI for testing the chatbot.

**What it does:**
- Creates a Gradio chat interface
- Connects to the FastAPI backend (`http://localhost:8000`)
- Provides a user-friendly chat interface

**When to run:** For local testing and development.

---

## 📁 File Requirements

### Google Drive Folder

**Folder ID:** `1af9TUTNrBSkaoHZrSyqYWSTYqk0UiER3`

**Required Files:**
- **PDF files** (`.pdf`) - Processed by `handle_gdrive.py`
- **DOCX files** (`.docx`) - Processed by `handle_gdrive.py`

**Setup:**
1. Create a Google Drive folder
2. Share it with the service account or make it publicly accessible
3. Add the folder ID to `handle_gdrive.py` (or make it configurable)
4. Set `GOOGLE_DRIVE_API` in `.env`

**Note:** Currently, the Google Drive integration is not actively used by the main agent, but the infrastructure exists.

---

### Local Data Files

#### `data/docs/` Directory
**Required Files:**
- `Karla.docx` - Information about the office dog
- `Mitarbeiter Kontext Neckarmedia.docx` - Employee context
- `Onlinemarketing.docx` - Online marketing information
- `Unnützes Wissen für NM Chatbot.docx` - Miscellaneous knowledge

**Format:** Microsoft Word documents (`.docx`)

**Usage:** These files can be processed by `handle_gdrive.py` if placed in a `docs/` directory, but they're currently stored locally in `data/docs/`.

---

#### `data/services.json`
**Purpose:** Structured service descriptions, workflow, and FAQs.

**Required Format:**
```json
{
  "about": "Company description...",
  "services": {
    "digital_analytics": {
      "description": "Service description..."
    },
    "seo": { ... },
    "sea": { ... },
    ...
  },
  "workflow": {
    "kennenlernen_problemverstaendnis": "Description...",
    ...
  },
  "faqs": {
    "was_unterscheidet_neckarmedia": "Answer...",
    ...
  }
}
```

**Usage:** Loaded by `agent.py` to answer service-related questions.

**When to update:** When services, workflow, or FAQs change.

---

#### `data/latest_info.json`
**Purpose:** Employee and founder information.

**Required Format:**
```json
{
  "founders": {
    "Kay": "Description...",
    "Johannes": "Description..."
  },
  "employees": {
    "Karla": "Description...",
    "Antonello": "Description...",
    ...
  }
}
```

**Usage:** Loaded by `agent.py` to answer questions about employees and founders.

**When to update:** When employee information changes or new employees join.

---

#### `data/blog_posts.json`
**Purpose:** Crawled blog posts from the website.

**Format:** Array of blog post objects:
```json
[
  {
    "url": "https://www.neckarmedia.com/...",
    "title": "Blog Post Title",
    "content": "Full text content...",
    "date": "15. April 2016"
  },
  ...
]
```

**Generated by:** `services/crawl_blog.py`

**Usage:** Imported into database by `services/insert_blog_db.py`

**When to update:** Run `crawl_blog.py` when new blog posts are published.

---

### Database Files

#### `neckarmedia.db`
**Purpose:** SQLite database storing blog articles with embeddings.

**Schema:**
```sql
CREATE TABLE blog_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    keywords TEXT,
    source_url TEXT,
    date TEXT,
    embedding TEXT  -- JSON-encoded vector embeddings
)
```

**Generated by:** `services/db_sql.py` (schema) + `services/insert_blog_db.py` (data) + `services/generate_embeddings_db.py` (embeddings)

---

#### `chroma_db/` (Optional)
**Purpose:** ChromaDB vector database for document embeddings (from Google Drive).

**Generated by:** `services/handle_gdrive.py`

**Note:** Currently not used by the main agent, but available for future document-based retrieval.

---

## 🔄 Setup Workflow

### Initial Setup (First Time)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Up Environment Variables**
   Create `.env` file:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   GOOGLE_DRIVE_API=your-google-drive-api-key
   ALLOWED_ORIGINS=*
   RATE_LIMIT_REQUESTS=20
   RATE_LIMIT_PERIOD=60
   ENVIRONMENT=development
   PUBLIC_MODE=true
   ```

3. **Download German spaCy Model** (if using `handle_gdrive.py`)
   ```bash
   python -m spacy download de_core_news_md
   ```

4. **Set Up Database Schema**
   ```bash
   python services/db_sql.py
   ```

5. **Crawl Blog Posts**
   ```bash
   python services/crawl_blog.py
   ```
   This creates `data/blog_posts.json`

6. **Insert Blog Posts into Database**
   ```bash
   python services/insert_blog_db.py
   ```
   This populates the database with articles, summaries, and keywords.

7. **Generate Embeddings**
   ```bash
   python services/generate_embeddings_db.py
   ```
   This computes and stores vector embeddings for semantic search.

8. **Verify Data Files**
   Ensure these files exist:
   - `data/services.json`
   - `data/latest_info.json`
   - `neckarmedia.db` (with data and embeddings)

9. **Start the API**
   ```bash
   python api.py
   ```
   Or use Docker:
   ```bash
   docker-compose up -d
   ```

10. **Test the System**
    ```bash
    curl -X POST http://localhost:8000/chat_response \
      -H "Content-Type: application/json" \
      -d '{"user_prompt": "What services does Neckarmedia offer?"}'
    ```

---

### Regular Updates

#### When New Blog Posts Are Published

1. **Crawl Latest Posts**
   ```bash
   python services/crawl_blog.py
   ```

2. **Update Database**
   ```bash
   python services/insert_blog_db.py
   ```
   (This will update existing articles and add new ones)

3. **Regenerate Embeddings for New Articles**
   ```bash
   python services/generate_embeddings_db.py
   ```
   (Only processes articles without embeddings)

#### When Employee Information Changes

1. **Update `data/latest_info.json`**
   Edit the file with new employee/founder information.

2. **No database update needed** - The agent loads this file directly.

#### When Services Change

1. **Update `data/services.json`**
   Edit the file with new service descriptions, workflow, or FAQs.

2. **No database update needed** - The agent loads this file directly.

---

## 🔀 Execution Flow

### Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA COLLECTION                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  1. crawl_blog.py                 │
        │     - Scrapes blog posts          │
        │     - Output: blog_posts.json     │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  2. db_sql.py                     │
        │     - Creates database schema     │
        │     - Output: neckarmedia.db     │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  3. insert_blog_db.py              │
        │     - Loads blog_posts.json       │
        │     - Generates summaries (GPT)  │
        │     - Extracts keywords          │
        │     - Inserts into DB            │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  4. generate_embeddings_db.py     │
        │     - Computes embeddings        │
        │     - Stores in DB               │
        └───────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ neckarmedia.db│
                    │  (Ready!)     │
                    └───────────────┘
```

### Query Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  api.py                           │
        │  - Rate limiting                  │
        │  - Input validation               │
        │  - CORS protection                │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  agent.py                         │
        │  - decide_tool_to_use()          │
        │    (LLM selects tool)             │
        └───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Tool 1:      │   │ Tool 2:      │   │ Tool 3:      │
│ Employee/    │   │ Blog Search  │   │ Jobs         │
│ Founder Info │   │ (Vector DB)  │   │ Scraper      │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   ▼                   │
        │      ┌────────────────────┐           │
        │      │ query_vector_      │           │
        │      │ search()           │           │
        │      │ - Computes query   │           │
        │      │   embedding        │           │
        │      │ - Cosine similarity│           │
        │      │ - Returns top-k    │           │
        │      └────────────────────┘           │
        │                                       │
        └───────────────────┼───────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  agent.py                         │
        │  - generate_chat_response()      │
        │  - Builds context from tool      │
        │  - Calls GPT with context        │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  api.py                           │
        │  - Returns response to user      │
        └───────────────────────────────────┘
```

### Tool Selection Logic

The agent uses an LLM (`decide_tool_to_use()`) to select the appropriate tool:

1. **Founder/Employee Info** → Questions about people
2. **Company References (SQLite)** → General company knowledge, blog articles, references
3. **Jobs Scraper** → Job postings and career information
4. **Service Offerings** → Services, workflow, FAQs

### Vector Search Process

When "Company References (SQLite)" is selected:

1. User query is encoded into an embedding using `sentence-transformers/all-MiniLM-L6-v2`
2. Cosine similarity is computed against all article embeddings in the database
3. Top-k articles (default: 3) are retrieved
4. Article titles, summaries, and URLs are returned as context
5. Context is sent to GPT along with the user query
6. GPT generates a response based on the retrieved context

---

## 🔧 Configuration Files

### `.env` File

Required environment variables:

```env
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-key-here

# Google Drive API Key (optional, for handle_gdrive.py)
GOOGLE_DRIVE_API=your-google-drive-api-key

# CORS Configuration
ALLOWED_ORIGINS=*

# Rate Limiting
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_PERIOD=60

# Environment
ENVIRONMENT=development  # or "production"
PUBLIC_MODE=true
```

---

## 📊 Data Flow Summary

| Script | Input | Output | Purpose |
|--------|-------|--------|---------|
| `crawl_blog.py` | Website URLs | `blog_posts.json` | Collect blog data |
| `db_sql.py` | - | `neckarmedia.db` (schema) | Initialize database |
| `insert_blog_db.py` | `blog_posts.json` | `neckarmedia.db` (data) | Populate database |
| `generate_embeddings_db.py` | `neckarmedia.db` | `neckarmedia.db` (embeddings) | Create search vectors |
| `agent.py` | User query + DB | Chat response | Generate answers |
| `api.py` | HTTP requests | HTTP responses | Serve API |

---

## 🚀 Quick Start Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` with `OPENAI_API_KEY`
- [ ] Run `python services/db_sql.py`
- [ ] Run `python services/crawl_blog.py`
- [ ] Run `python services/insert_blog_db.py`
- [ ] Run `python services/generate_embeddings_db.py`
- [ ] Verify `data/services.json` exists
- [ ] Verify `data/latest_info.json` exists
- [ ] Start API: `python api.py`
- [ ] Test: `curl -X POST http://localhost:8000/chat_response -H "Content-Type: application/json" -d '{"user_prompt": "Hello"}'`

---

## 📝 Notes

- The Google Drive integration (`handle_gdrive.py`) exists but is not currently used by the main agent
- Blog posts are the primary knowledge source for company references
- Employee/founder info and services are loaded from JSON files (no database needed)
- Job listings are scraped live (not stored in database)
- Embeddings use `all-MiniLM-L6-v2` model (multilingual, 384 dimensions)
- The system supports both German and English queries

---

## 🔍 Troubleshooting

**Database not found:**
- Run `services/db_sql.py` first

**No embeddings:**
- Run `services/generate_embeddings_db.py`

**API errors:**
- Check `.env` file exists and has `OPENAI_API_KEY`
- Verify `neckarmedia.db` exists and has data
- Check that `data/services.json` and `data/latest_info.json` exist

**Import errors:**
- Ensure you're in the project root directory
- Activate virtual environment: `source neckarvenv/bin/activate`

---

For deployment instructions, see `QUICK_START.md` and `README.md`.

