from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
from threading import Timer
import random
import string
import requests

app = Flask(__name__)

# Environment variables: GEMINI_API_KEY, GOOGLE_API_KEY, GOOGLE_CSE_ID must be set.
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
if not google_api_key or not google_cse_id:
    raise ValueError("GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set")

# Configure Gemini API.
genai.configure(api_key=gemini_api_key)

# Pre-configured Gemini models with fallback options.
models = {
    "pro2.0": genai.GenerativeModel("gemini-2.0-pro-exp-02-05"),
    "flash2.0": genai.GenerativeModel("gemini-2.0-flash-exp"),
    "pro1.5": genai.GenerativeModel("gemini-1.5-pro-002"),
    "flash1.5": genai.GenerativeModel("gemini-1.5-flash-8b-latest")
}

# Conversation history: {conversation_code: (timestamp, stored_prompt)}
conversation_history = {}
EXPIRATION_TIME = 3 * 60 * 60  # 3 hours
MAX_CHARS = 360

def clean_up_history():
    """Remove conversation history entries older than EXPIRATION_TIME."""
    current_time = time.time()
    expired_keys = [key for key, (timestamp, _) in conversation_history.items() 
                    if current_time - timestamp > EXPIRATION_TIME]
    for key in expired_keys:
        del conversation_history[key]

def schedule_cleanup():
    """Schedule history cleanup every 10 minutes."""
    Timer(600, clean_up_history).start()

schedule_cleanup()

def generate_conversation_id():
    """Generate a unique 3-character alphanumeric conversation ID."""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(3))

def get_real_time_data(query):
    """
    Uses the Google Custom Search JSON API to fetch live data for the query.
    """
    endpoint = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
        "q": query,
        "hl": "en",
        "gl": "us"
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    results = response.json()
    if "items" in results and len(results["items"]) > 0:
        snippet = results["items"][0].get("snippet", "No snippet found")
        return snippet
    return "No real-time data found."

@app.route('/ai', methods=['GET'])
def ai_response():
    global conversation_history

    raw_prompt = request.args.get('prompt', '').strip()
    if not raw_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    # Check for an optional conversation code (e.g., "#ght")
    conv_code = None
    prompt_body = raw_prompt
    if raw_prompt.startswith('#'):
        parts = raw_prompt.split(' ', 1)
        conv_code = parts[0][1:]
        prompt_body = parts[1].strip() if len(parts) > 1 else ""

    # If the prompt body starts with "search ", treat it as a real-time search query.
    if prompt_body.lower().startswith("search "):
        search_query = prompt_body[len("search "):].strip()
        real_time_context = get_real_time_data(search_query)
        # Explicitly instruct Gemini to use the provided real-time data.
        structured_prompt = (
            f"Using the real-time data provided below, answer the following question accurately and concisely (under {MAX_CHARS} characters).\n"
            f"Do not rely on default knowledge—base your answer solely on the data provided.\n\n"
            f"Real-Time Data: {real_time_context}\n\n"
            f"Question: {search_query}\n"
        )
        final_message = search_query
    else:
        # Process as a normal prompt with optional conversation history.
        structured_prompt = (
            f"Respond to the user informatively and concisely (under {MAX_CHARS} characters). "
            "Use the provided context history only for reference, and prioritize answering the user's current message.\n\n"
        )
        if conv_code and conv_code in conversation_history:
            structured_prompt += f"Context History: {conversation_history[conv_code][1]}\n\n"
        structured_prompt += f"Current Message: {prompt_body}\n"
        final_message = prompt_body

    response = None
    response_text = ""

    # Attempt to generate content using Gemini models with fallback.
    try:
        response = models["pro2.0"].generate_content(structured_prompt)
        response_text = f"Pro 2.0 Steve's Ghost says, \"{response.text.strip()}\""
    except Exception as e:
        if "429" in str(e):
            try:
                response = models["flash2.0"].generate_content(structured_prompt)
                response_text = f"Flash 2.0 Steve's Ghost says, \"{response.text.strip()}\""
            except Exception as e:
                if "429" in str(e):
                    try:
                        response = models["pro1.5"].generate_content(structured_prompt)
                        response_text = f"Pro 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                    except Exception as e:
                        if "429" in str(e):
                            try:
                                response = models["flash1.5"].generate_content(structured_prompt)
                                response_text = f"Flash 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                            except Exception as e:
                                return f"Error with all models: {str(e)}", 500
                        else:
                            return f"Error with Pro 1.5 model: {str(e)}", 500
                else:
                    return f"Error with Flash 2.0 model: {str(e)}", 500
        else:
            return f"Error with Pro 2.0 model: {str(e)}", 500

    if not response:
        return "No response from the model.", 500

    # Update conversation history.
    if conv_code:
        conversation_history[conv_code] = (time.time(), final_message)
        code_to_return = conv_code
    else:
        code_to_return = generate_conversation_id()
        conversation_history[code_to_return] = (time.time(), final_message)

    return f"{response_text} #{code_to_return}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
