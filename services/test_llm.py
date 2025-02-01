import glob
import docx
import os
import json
import shutil
import ollama
import requests
from dotenv import load_dotenv
from langdetect import detect
import spacy
from transformers import pipeline
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# File Paths
docx_files = glob.glob("docs/*.docx")
chroma_db_path = "./chroma_db"

# Load Language Model & Classifier
nlp = spacy.load("de_core_news_md")  # German NLP model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

SERVICE_CATEGORIES = [
    "Digital Analytics", "SEO", "SEA", "PLA", "CRO", "Content Marketing", "Social Media Marketing"
]

# ✅ Ensure ChromaDB is reset before re-indexing
if os.path.exists(chroma_db_path):
    shutil.rmtree(chroma_db_path)

print("🔄 ChromaDB reset. Reinitializing...")

# ✅ Reinitialize ChromaDB
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(collection_name="neckarmedia", embedding_function=embedding, persist_directory=chroma_db_path)

def extract_docx_text(docx_path):
    """Extract text from a DOCX file."""
    doc = docx.Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

def extract_keywords_llm(text, num_keywords=10):
    """Uses the local Mistral model via Ollama to generate relevant keywords."""
    prompt = f"Extract {num_keywords} relevant keywords summarizing this text. Output only keywords, separated by commas.\n\n{text[:1000]}"  # Limit input to 1000 characters

    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])

    if "message" in response and "content" in response["message"]:
        return response["message"]["content"].strip()
    
    return "Unknown"

def annotate_metadata(text, file_path):
    """Generate metadata for each document chunk."""
    metadata = {
        "url": str(file_path),
        "title": str(os.path.basename(file_path)),
        "category": "",
        "language": str(detect(text)),
        "keywords": extract_keywords_llm(text, num_keywords=10),  # ✅ LLM-extracted keywords
        "entities": ""
    }
    
    # Named Entity Recognition (NER)
    doc = nlp(text)
    metadata["entities"] = ", ".join([ent.text for ent in doc.ents])  

    # ✅ Limit input text for classifier (Avoids long text issues)
    prediction_text = text[:512] if len(text) > 512 else text
    prediction = classifier(prediction_text, candidate_labels=SERVICE_CATEGORIES)

    metadata["category"] = prediction["labels"][0] if "labels" in prediction else "Unknown"

    return metadata

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# ✅ Process only DOCX files
for file_path in docx_files:
    print(f"📄 Processing DOCX file: {file_path}")
    raw_text = extract_docx_text(file_path)
    docs = splitter.create_documents([raw_text])
    
    for d in docs:
        metadata = annotate_metadata(d.page_content, file_path)
        d.metadata = metadata  # ✅ Assign metadata directly
    
    db.add_texts([d.page_content for d in docs], [d.metadata for d in docs])

# ✅ Persist ChromaDB
db.persist()

# 🔍 Query ChromaDB
query = "Neckarmedia Services und Mitarbeiter"
results = db.similarity_search(query, k=10)

# ✅ Remove duplicate results
seen_texts = set()
filtered_results = []

for doc in results:
    content_snippet = doc.page_content[:300]
    if content_snippet not in seen_texts:
        seen_texts.add(content_snippet)
        filtered_results.append(doc)

print(f"{query}")
for i, doc in enumerate(filtered_results[:5]):  # ✅ Print up to 5 unique results
    print(f"\n--- Result {i+1} ---")
    print("URL:", doc.metadata.get("url"))
    print("Title:", doc.metadata.get("title"))
    print("Keywords:", doc.metadata.get("keywords"))
    print("Chunk text snippet:", doc.page_content[:300], "...")

print("✅ All DOCX files processed and indexed successfully!")
