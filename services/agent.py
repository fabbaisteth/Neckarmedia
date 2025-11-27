import json
import os
import requests
from bs4 import BeautifulSoup
import gradio as gr
from langchain_openai import OpenAI
from openai import OpenAI as OAI
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import sqlite3
import numpy as np

#TODO - Implement the tool selection logic for agent search blog articles with the new standardized keywords. 
# Use standardized keywords to cluster articles such as testimonials, case studies, employee stories, workshops

# Load .env file from the services directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Loading .env file from: {env_path}")
load_dotenv(dotenv_path=env_path)
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai_api_key = openai_api_key.strip()  # Remove any whitespace/newlines
    print(f"✅ OpenAI API Key loaded: {openai_api_key[:20]}...{openai_api_key[-4:]}")
client = OAI(api_key=openai_api_key)

# Database path relative to project root (one level up from services/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, "neckarmedia.db")
model = SentenceTransformer("all-MiniLM-L6-v2")
STANDARDIZED_KEYWORDS = []

def connect_db():
    """Connect to SQLite database."""
    return sqlite3.connect(DB_PATH)

def load_services():
    """Loads service descriptions from the JSON file."""
    services_path = os.path.join(PROJECT_ROOT, "data/services.json")
    with open(services_path, "r", encoding="utf-8") as f:
        return json.load(f)

SERVICES_DATA = load_services()

def scrape_job_offerings(url="https://www.neckarmedia.com/karriere"):
    """Scrapes job listings from Neckarmedia's careers page and returns structured data."""
    
    try:
        # 🌍 Fetch the webpage with a User-Agent to avoid bot blocks
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        
        if response.status_code != 200:
            print(f"❌ Failed to retrieve page. Status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # 🔍 Find all potential job listing sections
        job_sections = soup.find_all("div", class_="avia-section")

        jobs = []

        for section in job_sections:
            try:
                job_id = section.get("id", "").strip()
                if not job_id:
                    continue  # Skip sections without a valid ID
                
                title_tag = section.find("h2", class_="av-special-heading-tag")
                title = title_tag.get_text(strip=True) if title_tag else None

                profile_section = section.find("div", class_="avia_textblock")
                profile = "\n".join([p.get_text(strip=True) for p in profile_section.find_all("p")]) if profile_section else None

                apply_link = section.find("a", class_="avia-button")
                apply_url = apply_link.get("href") if apply_link else url  # Default to main careers page if no link

                # ✅ Drop empty job listings
                if title and profile and " " in profile:
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "profile": profile,
                        "apply_link": apply_url
                    })

            except Exception as e:
                print(f"⚠️ Error processing job section: {e}")

        return jobs if jobs else [{"error": "No valid job listings found."}]

    except Exception as e:
        print(f"🔥 Critical error scraping jobs: {e}")
        return [{"error": "Failed to scrape job listings due to an unexpected issue."}]

def query_vector_search(user_query, top_k=3):
    """Finds most relevant articles using vector similarity."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Compute embedding for the user query
    query_embedding = model.encode(user_query).tolist()

    cursor.execute("SELECT title, summary, source_url, embedding FROM blog_articles")
    articles = cursor.fetchall()

    # Compute cosine similarity
    scores = []
    for title, summary, source_url, embedding in articles:
        article_embedding = json.loads(embedding)
        similarity = np.dot(query_embedding, article_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(article_embedding))
        scores.append((similarity, title, summary, source_url))

    conn.close()

    # Sort and return top-k matches
    scores.sort(reverse=True, key=lambda x: x[0])
    return [{"title": x[1], "summary": x[2], "source_url": x[3]} for x in scores[:top_k]]

def agent_search_blog_articles(user_query):
    """Performs hybrid retrieval using vector search and FTS5."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1️⃣ - **Vector Search**
    vector_results = query_vector_search(user_query)
    if vector_results:
        return vector_results
    
    conn.close()
    return [{"message": "No relevant blog articles found."}]


def get_latest_info():
    """Retrieves structured employee/founder data from latest_info.json."""
    
    json_path = "data/latest_info.json"  # Ensure the correct relative path

    # ✅ Check if the file exists
    if not os.path.exists(json_path):
        print(f"❌ Error: JSON file not found at {json_path}")
        return {"error": "Employee data file is missing."}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            latest_data = json.load(f)
        
        print(f"📂 Loaded JSON successfully: {json_path}")
        print(f"🔎 JSON Contents: {latest_data}")

        # ✅ Send the entire JSON content to GPT
        return latest_data

    except json.JSONDecodeError as e:
        print(f"❌ JSON decoding error: {e}")
        return {"error": "Failed to parse employee data."}

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": "An unexpected issue occurred while loading employee data."}

def get_service_description():
    """Retrieves a service description using fuzzy matching."""
    return json.dumps(SERVICES_DATA, indent=2)

tools = [
    Tool(name="Founder/Employee Info", func=get_latest_info, description="Use this for questions about employees and founders."),
    Tool(name="Company References and Blog(SQLite)", func=agent_search_blog_articles, description="Use this for company knowledge, blog posts, and references."),
    Tool(name="Jobs Scraper", func=scrape_job_offerings, description="Use this to fetch live job listings."),
    Tool(name="Service Offerings", func=get_service_description, description="Use this to fetch company services, workflow or FAQs."),
]

def decide_tool_to_use(user_prompt):
    """Uses an LLM to decide the best tool based on the user's query."""
    decision_prompt = PromptTemplate(
        input_variables=["user_prompt"],
        template="""
        You are a helpful AI assistant that decides which tool to use for answering a query. 
        You have the following tools available:

        1. "Founder/Employee Info" - for questions about specific employees or founders.
        2. "Company References (SQLite)" - for general company knowledge, services, articles, and references.
        3. "Jobs Scraper" - for job postings and job requirements.
        4. "Service Offerings" - Use this if the user asks about what services Neckarmedia provides, workflow or FAQs.

        Based on the following user query, choose the most relevant tool:
        
        User Query: {user_prompt}

        Respond with ONLY the tool name in exact wording.
        """
    )

    llm = OpenAI(temperature=0.2, api_key=openai_api_key)
    response = llm.invoke(decision_prompt.format(user_prompt=user_prompt))

    selected_tool = response.strip().replace('"', '').replace("'", "")  # Remove quotes if present
    print(f"🔎 Tool decision output: {selected_tool}")

    # ✅ Ensure the tool name matches exactly
    valid_tools = {
        "Founder/Employee Info",
        "Company References (SQLite)",
        "Jobs Scraper",
        "Service Offerings"
    }

    if selected_tool in valid_tools:
        return selected_tool
    else:
        print(f"❌ Invalid tool selection: {selected_tool} (Check LLM output)")
        return None 
    
def generate_chat_response(user_query):
    """Handles tool selection and retrieves the appropriate response."""
    print(f"\n🤖 Received user query: {user_query}")

    selected_tool = decide_tool_to_use(user_query)
    print(f"🔧 Selected tool: {selected_tool}")
    


    if selected_tool == "Service Offerings":
        tool_output = get_service_description()
    elif selected_tool == "Founder/Employee Info":
        tool_output = get_latest_info()
    elif selected_tool == "Company References (SQLite)":
        tool_output = agent_search_blog_articles(user_query)
    elif selected_tool == "Jobs Scraper":
        tool_output = scrape_job_offerings()
    else:
        print(f"❌ No matching tool found for: {user_query}")
        return "I couldn't determine the best source for your query."

    print(f"📜 Retrieved tool output (first 500 chars):\n{str(tool_output)[:500]}...")

    context_text = tool_output if isinstance(tool_output, str) else json.dumps(tool_output, indent=2)

    system_prompt = f"""
    You are an employee of Neckarmedia, a creative and marketing agency. Answer questions informally,
    as if you were a real team member. Use the following context to provide responses. 
    If you don't know the answer, don't just say 'I don't know' – instead, direct the user to visit Neckarmedia's website or contact the team for more details. Feel free to add humor or ask follow-up questions
    Use the following structured data as context to generate informative answers.

    Context:
    {context_text}

    If the requested information is unavailable, direct users to Neckarmedia's official website https://www.neckarmedia.com.
    Keep responses professional, well-structured, and concise.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    print(f"💬 Sending request to GPT with system prompt (first 500 chars):\n{system_prompt[:500]}...")

    try:
        response = client.responses.create(
            model="gpt-5",
            input=messages,
            stream=False
        )

        answer = response.output_text
        if not answer:
            # If streaming didn't work, response might be an object
            print("⚠️  No content from streaming, trying to parse response object...")
            if hasattr(response, 'output'):
                for item in response.output:
                    if hasattr(item, 'text'):
                        answer += item.text
        
        print(f"📝 GPT Response ({len(answer)} chars): {answer[:200]}..." if len(answer) > 200 else f"📝 GPT Response: {answer}")

        if "I don't know" in answer or len(answer.strip()) < 5:
            answer = (
                "I'm not entirely sure, but you can check out Neckarmedia’s website for more details. "
                "\n\n👉 [Neckarmedia Website](https://neckarmedia.com)"
            )
            print(f"⚠️ GPT did not generate a confident response, redirecting user to website.")

        return answer

    except Exception as e:
        print(f"🔥 Error in GPT response generation: {e}")
        return "I'm currently unable to process your request. Please try again later."
