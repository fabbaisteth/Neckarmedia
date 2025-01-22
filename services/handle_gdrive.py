import glob
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

pdf_files = glob.glob("pdfs/*.pdf")
docx_files = glob.glob("docs/*.docx")
# etc.

def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text

def extract_docx_text(docx_path):
    d = docx.Document(docx_path)
    return "\n".join([p.text for p in d.paragraphs])

splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(
    collection_name="neckarmedia",
    embedding_function=embedding,
    persist_directory="./chroma_db"
)

for pdf_path in pdf_files:
    raw_text = extract_pdf_text(pdf_path)
    docs = splitter.create_documents([raw_text])
    for d in docs:
        d.metadata["source"] = pdf_path
    # batch add:
    db.add_texts([d.page_content for d in docs], [d.metadata for d in docs])

for docx_path in docx_files:
    raw_text = extract_docx_text(docx_path)
    docs = splitter.create_documents([raw_text])
    for d in docs:
        d.metadata["source"] = docx_path
    db.add_texts([d.page_content for d in docs], [d.metadata for d in docs])

db.persist()
