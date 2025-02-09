from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
from threading import Timer
import random
import string

app = Flask(__name__)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=api_key)

models = {
    "pro2.0": genai.GenerativeModel("gemini-2.0-pro-exp-02-05"),
    "flash2.0": genai.GenerativeModel("gemini-2.0-flash-exp"),
    "pro1.5": genai.GenerativeModel("gemini-1.5-pro-002"),
    "flash1.5": genai.GenerativeModel("gemini-1.5-flash-8b-latest")
}

conversation_history = {}
EXPIRATION_TIME = 3 * 60 * 60  # 3 hours
MAX_CHARS = 360

def clean_up_history():
    """Periodically clean up expired conversation history."""
    current_time = time.time()
    expired_keys = [key for key, (timestamp, _) in conversation_history.items() if current_time - timestamp > EXPIRATION_TIME]
    for key in expired_keys:
        del conversation_history[key]

def schedule_cleanup():
    """Schedule the cleanup task every 10 minutes."""
    Timer(600, clean_up_history).start()

schedule_cleanup()

def generate_conversation_id():
    """Generate a unique 3-character alphanumeric conversation ID."""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for _ in range(3))

@app.route('/ai', methods=['GET'])
def ai_response():
    global conversation_history

    raw_prompt = request.args.get('prompt', '').strip()
    if not raw_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    code = None
    new_prompt = raw_prompt

    if raw_prompt.startswith('#'):
        parts = raw_prompt.split(' ', 1)
        code = parts[0][1:]
        new_prompt = parts[1].strip() if len(parts) > 1 else ""

    context_history = ""
    if code:
        if code in conversation_history:
            context_history = conversation_history[code][1]  # Retrieve the stored context
        else:
            # If the code doesn't exist, treat it as a new prompt
            code = None

    structured_prompt = (
        f"Respond to the user informatively and concisely, keeping the response under {MAX_CHARS} characters. "
        "Use the provided context history only for reference, and prioritize answering the user's current message.\n\n"
    )
    if context_history:
        structured_prompt += f"Context History: {context_history}\n\n"
    structured_prompt += f"Current Message: {new_prompt}\n"

    response = None
    model_used = None
    response_text = ""

    # Try using Gemini Pro 2.0 first, then fallback in order.
    try:
        response = models["pro2.0"].generate_content(structured_prompt)
        response_text = f"Pro 2.0 Steve's Ghost says, \"{response.text.strip()}\""
        model_used = "pro-2.0"
    except Exception as e:
        if "429" in str(e):  # Rate limit error; try next model.
            try:
                response = models["flash2.0"].generate_content(structured_prompt)
                response_text = f"Flash 2.0 Steve's Ghost says, \"{response.text.strip()}\""
                model_used = "flash-2.0"
            except Exception as e:
                if "429" in str(e):
                    try:
                        response = models["pro1.5"].generate_content(structured_prompt)
                        response_text = f"Pro 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                        model_used = "pro-1.5"
                    except Exception as e:
                        if "429" in str(e):
                            try:
                                response = models["flash1.5"].generate_content(structured_prompt)
                                response_text = f"Flash 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                                model_used = "flash-1.5"
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

    if not code:
        code = generate_conversation_id()

    conversation_history[code] = (time.time(), new_prompt)
    return f"{response_text} #{code}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
