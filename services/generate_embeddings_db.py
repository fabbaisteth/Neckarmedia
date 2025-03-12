from sentence_transformers import SentenceTransformer
import sqlite3
import json

model = SentenceTransformer("all-MiniLM-L6-v2")

conn = sqlite3.connect("neckarmedia.db")
cursor = conn.cursor()

cursor.execute("SELECT id, content FROM blog_articles")
articles = cursor.fetchall()

for article_id, content in articles:
    embedding = model.encode(content).tolist()
    cursor.execute("UPDATE blog_articles SET embedding = ? WHERE id = ?", (json.dumps(embedding), article_id))

conn.commit()
conn.close()
