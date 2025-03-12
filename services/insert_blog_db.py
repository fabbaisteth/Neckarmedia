import json
import os
import sqlite3
import re
from openai import OpenAI as OAI
from dotenv import load_dotenv

# ✅ Load API Key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OAI()

with open("services.json", "r", encoding="utf-8") as f:
    SERVICE_DATA = json.load(f)
STANDARDIZED_KEYWORDS = list(SERVICE_DATA["services"].keys()) + ["case study", "testimonial", "client", "reference", "feedback"]

# ✅ Define Database Setup
def setup_database():
    """Creates an SQLite database and initializes tables if they don't exist."""
    conn = sqlite3.connect("neckarmedia.db")
    cursor = conn.cursor()

    # Create a table for blog articles with summary and keywords
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT, 
            keywords TEXT, 
            source_url TEXT,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database setup complete.")

def extract_keywords(text):
    """Extracts standardized keywords from text, ensuring whole-word matches."""
    text = text.lower()
    found_keywords = set()

    for kw in STANDARDIZED_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text):  # Ensure whole-word match
            found_keywords.add(kw)

    return ", ".join(found_keywords) if found_keywords else "miscellaneous"

def enrich_blog_content(title, content):
    """Uses GPT-4 to generate a summary, extract company names, and assign keywords."""
    
    prompt = f"""
    **Task:** Summarize this blog article, extract relevant company names, and assign standardized keywords.
    
    **Blog Title:** {title}

    **Content:** {content[:2000]}  # Limit to avoid token overflow

    **Instructions:**
    1. Summarize the article in 3-4 sentences.
    2. Extract any **company names** from the text.
    3. Assign relevant keywords from this list: {", ".join(STANDARDIZED_KEYWORDS)}.
    4. If the article is about a **client reference, case study, or testimonial**, include `"case study"`, `"client"`, or `"reference"` as keywords.
    
    **Format:**
    Summary: <summary>
    Companies: <comma-separated company names>
    Keywords: <comma-separated keywords>
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You extract summaries, company names, and keywords from articles."},
                  {"role": "user", "content": prompt}],
        temperature=0.5
    )

    result_text = response.choices[0].message.content.strip()

    try:
        summary = re.search(r"Summary:\s*(.*)", result_text).group(1).strip()
        companies = re.search(r"Companies:\s*(.*)", result_text).group(1).strip()
        keywords = re.search(r"Keywords:\s*(.*)", result_text).group(1).strip()
    except AttributeError:
        summary, companies, keywords = "No summary available", "", "miscellaneous"

    # ✅ Ensure non-empty keywords and prevent duplicates
    extracted_keywords = extract_keywords(content)  # Standardized keyword extraction
    all_keywords = list(set(keywords.split(", ") + extracted_keywords.split(", ")))  # Avoid duplicates

    return summary, ", ".join(all_keywords)

def insert_or_update_blog_article(title, content, source_url, date):
    """Inserts a new blog article or updates only the summary and keywords."""
    summary, keywords = enrich_blog_content(title, content)

    conn = sqlite3.connect("neckarmedia.db")
    cursor = conn.cursor()

    # ✅ First, check if the article already exists
    cursor.execute("SELECT id FROM blog_articles WHERE title = ?", (title,))
    existing_article = cursor.fetchone()

    if existing_article:
        # ✅ If exists, only update summary and keywords
        cursor.execute("""
            UPDATE blog_articles 
            SET summary = ?, keywords = ? 
            WHERE title = ?
        """, (summary, keywords, title))
        print(f"🔄 Updated summary/keywords for: {title}")

    else:
        # ✅ If not exists, insert new article
        cursor.execute("""
            INSERT INTO blog_articles (title, content, summary, keywords, source_url, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, content, summary, keywords, source_url, date))
        print(f"✅ Inserted new article: {title}")

    conn.commit()
    conn.close()

# ✅ Load Blog Articles from JSON
def load_articles_from_json(json_path="blog_posts.json"):
    """Loads blog articles from a JSON file and inserts them into the database."""
    
    if not os.path.exists(json_path):
        print(f"❌ Error: JSON file not found at {json_path}")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
        
        print(f"📂 Loaded {len(articles)} blog articles from {json_path}")

        for article in articles:
            title = article.get("title", "Untitled")
            content = article.get("content", "No content available")
            source_url = article.get("url", "No URL")
            date = article.get("date", "Unknown Date")

            insert_or_update_blog_article(title, content, source_url, date)

    except json.JSONDecodeError as e:
        print(f"❌ JSON decoding error: {e}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# ✅ Run the Setup & Load Articles
if __name__ == "__main__":
    setup_database()
    load_articles_from_json()
