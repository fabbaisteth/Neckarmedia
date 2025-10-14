import gradio as gr
import requests
import json

# API endpoint configuration
API_URL = "http://localhost:8000/chat_response"

def chat_with_api(user_input, chat_history):
    """
    Sends user input to the FastAPI backend and returns the response.
    
    Args:
        user_input: The user's message
        chat_history: List of [user_msg, bot_msg] pairs
        
    Returns:
        Tuple of (empty_string, updated_chat_history)
    """
    if not user_input.strip():
        return "", chat_history
    
    try:
        # Call the FastAPI endpoint
        response = requests.post(
            API_URL,
            json={"user_prompt": user_input},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get("response", "No response received from API")
        else:
            bot_response = f"❌ Error: API returned status code {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        bot_response = "❌ Error: Could not connect to API. Make sure the API server is running on http://localhost:8000"
    except requests.exceptions.Timeout:
        bot_response = "❌ Error: Request timed out. Please try again."
    except Exception as e:
        bot_response = f"❌ Error: {str(e)}"
    
    # Append to chat history
    chat_history.append((user_input, bot_response))
    return "", chat_history

# Create Gradio interface
with gr.Blocks(title="Neckarmedia Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🤖 Neckarmedia Chatbot
        
        Ask me anything about Neckarmedia - services, employees, blog articles, job openings, and more!
        
        **Note:** Make sure the API server is running on `http://localhost:8000` before using this interface.
        """
    )
    
    with gr.Row():
        with gr.Column():
            chatbot = gr.Chatbot(
                label="Chat with Neckarmedia AI Assistant",
                height=500,
                bubble_full_width=False
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Type your message here...",
                    placeholder="e.g., What services does Neckarmedia offer?",
                    scale=4
                )
                submit_btn = gr.Button("Send", scale=1, variant="primary")
            
            clear = gr.Button("Clear Chat", variant="secondary")
    
    gr.Markdown(
        """
        ### Example Questions:
        - What services does Neckarmedia offer?
        - Who are the founders of Neckarmedia?
        - Are there any job openings?
        - Tell me about recent blog posts
        - What is the company's workflow?
        """
    )
    
    # Event handlers
    msg.submit(chat_with_api, [msg, chatbot], [msg, chatbot])
    submit_btn.click(chat_with_api, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

