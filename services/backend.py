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
    seen_texts = set()
    unique_results = []
    for result in results:
        content_snippet = result.page_content[:300]  # Use first 300 characters for comparison
        if content_snippet not in seen_texts:
            seen_texts.add(content_snippet)
            unique_results.append(result.page_content)
    
    return unique_results

def generate_chat_response(user_query: str) -> str:
    """
    1. Get top K relevant documents from Chroma.
    2. Build a prompt to include them as context.
    3. Call OpenAI API to get the response.
    """
    # Retrieve top matches
    context_docs = get_relevant_context(user_query, n_results=5)
    
    # Build a single string with the top context
    context_text = "\n\n".join(context_docs) if context_docs else ""
    
    # Construct the system prompt
    system_prompt = (
        "You are an employee of Neckarmedia, a creative and marketing agency. Answer questions informally, "
        "as if you were a real team member. Use the following context to provide responses. "
        "If you don't know the answer, don't just say 'I don't know' – instead, direct the user to visit "
        "Neckarmedia's website or contact the team for more details. Feel free to add humor or ask follow-up questions!\n\n"
        f"Context:\n{context_text}\n\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    # Call OpenAI ChatCompletion endpoint
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7  # Slightly higher temperature for a more natural tone
    )

    answer = response.choices[0].message.content
    
    # If no relevant response, redirect to the website
    if "I don't know" in answer or len(answer.strip()) < 5:
        answer = (
            "Hmm, that's a great question! I'm not 100% sure, but you should definitely check out our website "
            "or reach out to the team at Neckarmedia – they'd love to help! \n\n👉 [Neckarmedia Website](https://neckarmedia.com)"
        )
    
    return answer

