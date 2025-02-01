import glob
import PyPDF2
import docx
import os
import requests
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from dotenv import load_dotenv
from langdetect import detect
import spacy
from transformers import pipeline
import shutil

load_dotenv()

pdf_files = glob.glob("pdfs/*.pdf")
docx_files = glob.glob("docs/*.docx")
API_KEY = os.getenv("GOOGLE_DRIVE_API")
FOLDER_ID = "1af9TUTNrBSkaoHZrSyqYWSTYqk0UiER3"

nlp = spacy.load("de_core_news_md")  # German model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

SERVICE_CATEGORIES = [
    "Digital Analytics", "SEO", "SEA", "PLA", "CRO", "Content Marketing", "Social Media Marketing"
]
chroma_db_path = "./chroma_db"

if os.path.exists(chroma_db_path):
    shutil.rmtree(chroma_db_path)  # Deletes the existing database

print("ChromaDB reset. Reinitializing...")

# Reinitialize ChromaDB collection
db = Chroma(
    collection_name="neckarmedia",
    embedding_function=embedding,
    persist_directory=chroma_db_path
)

def list_folder_files(folder_id, api_key=API_KEY):
    base_url = "https://www.googleapis.com/drive/v3/files"
    params = {"q": f"'{folder_id}' in parents and trashed=false", "key": api_key, "fields": "files(id, name, mimeType)"}
    r = requests.get(base_url, params=params)
    data = r.json()
    return data.get("files", [])

def download_file(file_id, local_path, api_key=API_KEY):
    download_url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&key={api_key}"
    r = requests.get(download_url)
    if r.status_code == 200:
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Saved {file_id}")

def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
    return text

def extract_docx_text(docx_path):
    d = docx.Document(docx_path)
    return "\n".join([p.text for p in d.paragraphs])

def annotate_metadata(text, file_path):
    metadata = {
        "url": file_path,
        "title": os.path.basename(file_path),
        "category": "",
        "language": str(detect(text)),
        "keywords": "",
        "entities": ""
    }
    
    doc = nlp(text)
    metadata["entities"] = ", ".join([ent.text for ent in doc.ents])  # Convert list to string
    
    # Use Hugging Face model for category prediction
    prediction = classifier(text, candidate_labels=SERVICE_CATEGORIES)
    metadata["category"] = prediction["labels"][0] if "labels" in prediction else "Unknown"  # Handle missing keys safely
    metadata["keywords"] = ", ".join(set(text.split()[:10]))  # Simple keyword extraction
    
    return metadata

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(collection_name="neckarmedia", embedding_function=embedding, persist_directory="./chroma_db")

for pdf_path in pdf_files:
    raw_text = extract_pdf_text(pdf_path)
    docs = splitter.create_documents([raw_text])
    for d in docs:
        d.metadata = filter_complex_metadata(annotate_metadata(d.page_content, pdf_path))
    db.add_texts([d.page_content for d in docs], [d.metadata for d in docs])

for docx_path in docx_files:
    raw_text = extract_docx_text(docx_path)
    docs = splitter.create_documents([raw_text])
    for d in docs:
        metadata = annotate_metadata(d.page_content, docx_path)  # Ensure metadata is a dictionary
        d.metadata = filter_complex_metadata(metadata)  # Apply filtering to a dictionary
    db.add_texts([d.page_content for d in docs], [d.metadata for d in docs])


db.persist()
