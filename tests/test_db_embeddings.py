
import sqlite3
from sentence_transformers import SentenceTransformer
import json
import numpy as np

DB_PATH = "neckarmedia.db"

model = SentenceTransformer("all-MiniLM-L6-v2")

def query_vector_search(user_query, top_k=3):
    """Finds most relevant articles using vector similarity."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Compute embedding for the user query
    query_embedding = model.encode(user_query).tolist()

    cursor.execute("SELECT title, summary, source_url, embedding FROM blog_articles")
    articles = cursor.fetchall()

    # Compute cosine similarity
    scores = []
    for title, summary, source_url, embedding in articles:
        article_embedding = json.loads(embedding)
        similarity = np.dot(query_embedding, article_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding))
        scores.append((similarity, title, summary, source_url))

    conn.close()

    # Sort and return top-k matches
    scores.sort(reverse=True, key=lambda x: x[0])
    return [{"title": x[1], "summary": x[2], "source_url": x[3]} for x in scores[:top_k]]

def agent_search_blog_articles(user_query):
    """Performs hybrid retrieval using vector search and FTS5."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1️⃣ - **Vector Search**
    vector_results = query_vector_search(user_query)
    if vector_results:
        return vector_results

    # 2️⃣ - **FTS5 Full-Text Search**
    sanitized_query = user_query.replace("'", "''")  # Prevent SQL injection
    fts_query = f"""
        SELECT title, summary, source_url FROM blog_articles_fts 
        WHERE blog_articles_fts MATCH '{sanitized_query}'
        LIMIT 3
    """
    
    try:
        cursor.execute(fts_query)
        results = cursor.fetchall()
        if results:
            conn.close()
            return [{"title": row[0], "summary": row[1], "source_url": row[2]} for row in results]
    except sqlite3.OperationalError as e:
        print(f"❌ SQLite FTS5 Error: {e}")

    conn.close()
    return [{"message": "No relevant blog articles found."}]

if __name__ == "__main__":
    user_query = input("Enter your search query: ")
    results = agent_search_blog_articles(user_query)
    print(json.dumps(results, indent=2))
