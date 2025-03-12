import json

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from unittest.mock import patch
from bs4 import BeautifulSoup
from services.agent import scrape_job_offerings, vector_search_tool, get_latest_info  # Import functions

# Initialize the embedding model (replace with OpenAI for better results)
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load ChromaDB
db = Chroma(
    collection_name="neckarmedia",
    embedding_function=embedding_model,
    persist_directory="chroma_db"
)

# ---- 2️⃣ TEST VECTOR SEARCH TOOL ----
def test_vector_search_tool():
    """Test vector retrieval against the actual ChromaDB."""
    results = vector_search_tool("AI marketing", 2)  # Query actual DB

    assert len(results) > 0, "No results found in ChromaDB!"
    
    for result in results:
        assert "content" in result
        assert "source" in result
        print(f"✅ Found: {result['content']} (Source: {result['source']})")

# ---- 3️⃣ TEST LATEST INFO RETRIEVAL ----
@patch("builtins.open", create=True)
@patch("json.load")
def test_get_latest_info(mock_json_load, mock_open):
    """Test retrieval from structured JSON file."""
    mock_json_load.return_value = {
        "founders": {"John Doe": "Founder of Neckarmedia"},
        "employees": {"Jane Smith": "Head of AI Research"}
    }

    result_founder = get_latest_info("Who is John Doe?")
    result_employee = get_latest_info("Tell me about Jane Smith")

    assert result_founder == "Founder of Neckarmedia"
    assert result_employee == "Head of AI Research"

    # Test missing entry
    result_not_found = get_latest_info("Unknown person")
    assert result_not_found == "Sorry, I couldn't find the information in the latest records."

def test_scrape_live_job_offerings():
    """Test scraping job offerings and ensure a valid list is returned."""
    job_results = scrape_job_offerings()

    # Ensure the result is a list
    assert isinstance(job_results, list), "Expected a list, but got something else."

    # Ensure there's at least one job or a failure message
    assert len(job_results) > 0, "No job listings found."

    # Check that each job entry contains the expected keys
    for job in job_results:
        assert "id" in job, "ID are missing."
        assert "title" in job, "Job title is missing."
        assert "profile" in job, "Profile section is missing."
        assert "apply_link" in job, "Application link is missing."

    print("\n✅ Live job offerings scraped successfully:")
    for job in job_results:
        print(f"- {job['title']} | Apply: {job['apply_link']}")
