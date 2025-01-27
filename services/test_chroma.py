from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Load your local embeddings again
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Reconnect to the same Chroma store
db = Chroma(
    collection_name="neckarmedia",
    embedding_function=embeddings,
    persist_directory="chroma_db"
)

query = "Homeoffice"
results = db.similarity_search(query, k=5)
print(f"{query}")
for i, doc in enumerate(results):
    print(f"\n--- Result {i+1} ---")
    print("URL:", doc.metadata.get("url"))
    print("Title:", doc.metadata.get("title"))
    print("Chunk text snippet:", doc.page_content[:300], "...")
