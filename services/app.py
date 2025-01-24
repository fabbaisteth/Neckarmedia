import gradio as gr 
from backend import generate_chat_response

def chat_interface(user_input, chat_history):
    """
    This function will be called every time a user sends a message in the Gradio interface.
    'chat_history' holds the conversation so far (list of [user_msg, bot_msg] pairs).
    """
    # Get model's response
    response = generate_chat_response(user_input)

    # Append to chat history
    chat_history.append((user_input, response))
    return "", chat_history  # Return empty input, updated chat history

with gr.Blocks() as demo:
    gr.Markdown("# Neckarmedia Chatbot")

    chatbot = gr.Chatbot(label="Chat with RAG + OpenAI")
    msg = gr.Textbox(label="Type your message here...")
    clear = gr.Button("Clear Chat")

    # Whenever the user hits enter in the textbox, call 'chat_interface'
    msg.submit(chat_interface, [msg, chatbot], [msg, chatbot])

    # Clear button to reset the chat
    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch(server_name="0.0.0.0", server_port=7860)
