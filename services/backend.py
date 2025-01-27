import os
from openai import OpenAI
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv 
load_dotenv()
client = OpenAI()

def get_relevant_context(query: str, n_results: int = 3) -> List[str]:
    """
    Embeds the user query, retrieves top-n semantic matches from Chroma, 
    and returns the text of those matches.
    """
    query_embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    db = Chroma(
    collection_name="neckarmedia",
    embedding_function=query_embedding,
    persist_directory="chroma_db"
    )

    results = db.similarity_search(query, k=n_results)
    # results["documents"] is a list of lists (because each query can return multiple docs)
    # We only have 1 query, so results["documents"][0] is the top matches for that query
    return [result.page_content for result in results]

def generate_chat_response(user_query: str) -> str:
    """
    1. Get top K relevant documents from Chroma.
    2. Build a prompt to include them as context.
    3. Call OpenAI API to get the response.
    """
    # Retrieve top matches
    context_docs = get_relevant_context(user_query, n_results=5)

    # Build a single string with the top context
    # Each chunk is appended with a separator, like '---' or '\n\n'
    context_text = "\n\n".join(context_docs)

    # Construct the prompt
    system_prompt = (
        "You are a helpful assistant. Use the following context to answer "
        "the user's question as accurately as possible. If the context doesn't have the answer, "
        "say you don't know.\n\n"
        f"Context:\n{context_text}\n\n"
    )

    # We'll use ChatCompletion with role-based messages:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    # Call the OpenAI ChatCompletion endpoint
    response = client.chat.completions.create(
        model="gpt-4o",  # or 'gpt-4', etc
        messages=messages,
        temperature=0.2
    )

    # Extract the assistant message
    answer = response.choices[0].message.content
    return answer
