import sqlite3

DB_PATH = "neckarmedia.db"

def get_unique_keywords():
    """Fetches all unique keywords from the blog_articles table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT keywords FROM blog_articles WHERE keywords IS NOT NULL")
    rows = cursor.fetchall()

    unique_keywords = set()
    
    for row in rows:
        if row[0]:  # Ensure it's not None
            keywords = row[0].split(",")  # Assuming comma-separated keywords
            unique_keywords.update(k.strip().lower() for k in keywords)  # Normalize case & trim spaces

    conn.close()
    
    return sorted(unique_keywords)  # Return sorted list for readability

# Run and display results
unique_keywords = get_unique_keywords()
print(f"✅ Found {len(unique_keywords)} unique keywords:\n", unique_keywords)
