import sqlite3

user_query = "Which companies did Neckarmedia consult?"

def search_blog_articles(user_query, n_results=3):
    """Performs a full-text search in SQLite for blog articles related to the user's query."""
    
    conn = sqlite3.connect("neckarmedia.db")
    cursor = conn.cursor()

    query = f"""
    SELECT title, summary, source_url 
    FROM blog_articles 
    WHERE title LIKE ? OR content LIKE ? OR keywords LIKE ?
    ORDER BY LENGTH(content) DESC 
    LIMIT ?;
    """

    # Using `%` wildcard for partial matches in SQLite
    params = (f"%{user_query}%", f"%{user_query}%", f"%{user_query}%", n_results)
    cursor.execute(query, params)

    results = cursor.fetchall()
    conn.close()

    # Format output
    if not results:
        return [{"message": "No relevant blog articles found."}]

    return [
        {"title": title, "summary": summary, "source_url": source_url}
        for title, summary, source_url in results
    ]

# 🔹 Test Example
print(search_blog_articles("AI marketing"))
