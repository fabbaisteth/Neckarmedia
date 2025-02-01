from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load embeddings model
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Reconnect to the same Chroma store
db = Chroma(
    collection_name="neckarmedia",
    embedding_function=embeddings,
    persist_directory="chroma_db"
)

queries = [
    "Who works at Neckarmedia",
    "Find references to Google Ads",
    "Show me documents about SEO"
]
for query in queries:
    print(f"\n🔎 **Query:** {query}")
    
    results = db.similarity_search(query, k=10)  # Retrieve top 10 results per query

    # Set to track unique content per query
    seen_texts = set()
    filtered_results = []

    # Filter out exact duplicate texts
    for doc in results:
        content_snippet = doc.page_content[:200]  # Use the first 300 characters for uniqueness check
        if content_snippet not in seen_texts:
            seen_texts.add(content_snippet)
            filtered_results.append(doc)

    # Print final unique results
    for i, doc in enumerate(filtered_results[:4]):  # Limit output to top 5 unique results per query
        print(f"\n--- Result {i+1} ---")
        print("URL:", doc.metadata.get("url"))
        print("Title:", doc.metadata.get("title"))
        print("Keywords:", doc.metadata.get("keywords"))
        print("Chunk text snippet:", doc.page_content[:300], "...")
