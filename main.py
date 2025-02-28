from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
from threading import Timer
import random
import string
import requests
import numpy as np
import openai  # For embeddings
from sentence_transformers import SentenceTransformer # For Embeddings

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
#openai.api_key = os.getenv("OPENAI_EMBEDDING_API_KEY", gemini_api_key)  # Model is paid
embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")

# Pre-configured Gemini models with fallback options.
models = {
    "pro2.0": genai.GenerativeModel("gemini-2.0-pro-exp-02-05"),
    "flash2.0": genai.GenerativeModel("gemini-2.0-flash"),
    "pro1.5": genai.GenerativeModel("gemini-1.5-pro-latest"),
    "flash1.5": genai.GenerativeModel("gemini-1.5-flash-latest")
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

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_embedding(text):
    """Returns a numpy array embedding of the input text."""
    return embeddings_model.encode(text)

def get_real_time_data(query):
    """
    Uses the Google Custom Search JSON API to fetch live data for the query.
    Retrieves multiple items, splits them into sentences, and then selects the top relevant sentences.
    """
    endpoint = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": google_api_key,
        "cx": google_cse_id,
        "q": query,
        "hl": "en",
        "gl": "us",
        "num": 3  # Retrieve top 3 results.
    }
    response = requests.get(endpoint, params=params)
    response.raise_for_status()
    results = response.json()
    print("DEBUG: Google Custom Search response:", results)
    
    # Collect all snippets
    all_snippets = []
    if "items" in results:
        for item in results["items"]:
            snippet = item.get("snippet", "")
            if snippet:
                all_snippets.append(snippet)
    combined_text = " ".join(all_snippets)
    print("DEBUG: Combined snippet text:", combined_text)
    
    # Split into sentences (a simple split by period; for production use a robust method)
    sentences = [s.strip() for s in combined_text.split('.') if s.strip()]
    if not sentences:
        return "No real-time data found."
    
    # Get embedding for the query
    query_embedding = get_embedding(query)
    
    # Compute similarity for each sentence
    sentence_similarities = []
    for sentence in sentences:
        emb = get_embedding(sentence)
        similarity = cosine_similarity(query_embedding, emb)
        sentence_similarities.append((sentence, similarity))
    
    # Sort sentences by similarity descending and pick top 3
    sentence_similarities.sort(key=lambda x: x[1], reverse=True)
    top_sentences = [s for s, sim in sentence_similarities[:3]]
    
    refined_context = " ".join(top_sentences)
    print("DEBUG: Refined context for Gemini:", refined_context)
    return refined_context

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

    # Determine if this is a real-time search query.
    if prompt_body.lower().startswith("search "):
        search_query = prompt_body[len("search "):].strip()
        real_time_context = get_real_time_data(search_query)
        structured_prompt = (
            f"Based solely on the real-time data provided below, extract and provide a direct, specific answer to the following question. "
            f"Answer in one concise sentence (under {MAX_CHARS} characters). Do not rely on any external knowledge.\n\n"
            f"Real-Time Data: {real_time_context}\n\n"
            f"Question: {search_query}\n"
        )
        final_message = search_query
    else:
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

    # Try Gemini models with fallback.
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
