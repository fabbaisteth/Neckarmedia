import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer

DB_PATH = "neckarmedia.db"

model = SentenceTransformer("all-MiniLM-L6-v2")

# def setup_database():
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()

#     # 1️⃣ **Create FTS5 Virtual Table**

#     cursor.execute("""
#         ALTER TABLE blog_articles ADD COLUMN embeding TEXT
#                    """)

#     conn.commit()
#     conn.close()

#     print("✅ Created embedding column.")

def store_embeddings():
    """Compute and store embeddings for existing articles."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT title, content FROM blog_articles WHERE embedding IS NULL")
    articles = cursor.fetchall()

    for article_title, content in articles:
        embedding = model.encode(content).tolist()
        cursor.execute("UPDATE blog_articles SET embedding = ? WHERE title = ?", (json.dumps(embedding), article_title))

    conn.commit()
    conn.close()
    print(f"✅ {len(articles)} embeddings stored.")

# Run setup & generate embeddings
if __name__ == "__main__":
    # setup_database()
    store_embeddings()