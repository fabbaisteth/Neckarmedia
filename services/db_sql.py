import sqlite3

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
            source_url TEXT
        )
    """)

    conn.commit()
    conn.close()

setup_database()


