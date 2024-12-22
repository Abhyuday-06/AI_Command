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
    "flash2.0": genai.GenerativeModel("gemini-2.0-flash-exp"),
    "pro": genai.GenerativeModel("gemini-1.5-pro-002"),
    "flash1.5": genai.GenerativeModel("gemini-1.5-flash-8b-latest")
}

conversation_history = {}
EXPIRATION_TIME = 3 * 60 * 60  # 3 hours
MAX_CHARS = 390 # Maximum characters for the response

def clean_up_history():
    current_time = time.time()
    expired_keys = [key for key, (timestamp, _) in conversation_history.items() if current_time - timestamp > EXPIRATION_TIME]
    for key in expired_keys:
        del conversation_history[key]

def schedule_cleanup():
    Timer(600, clean_up_history).start()

schedule_cleanup()

def generate_conversation_id():
    return ''.join(random.choice(string.ascii_letters) for i in range(3))

@app.route('/ai', methods=['GET'])
def ai_response():
    global conversation_history
    raw_prompt = request.args.get('prompt', '')
    if not raw_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    if raw_prompt.startswith('#'):
        parts = raw_prompt.split(' ', 1)
        code = parts[0][1:]
        new_prompt = parts[1].strip() if len(parts) > 1 else ''
    else:
        code = None
        new_prompt = raw_prompt.strip()

    if code and code not in conversation_history:
        return f"Invalid conversation ID: #{code}", 400

    context_history = ""
    if code and conversation_history:
        context_list = []
        for key, (_, value) in conversation_history.items():
            if key == code:
                context_list.append(value)
                break
        if context_list:
            context_history = "\n".join(context_list)
        else:
            return f"Invalid conversation ID: #{code}", 400

    structured_prompt = (
        f"Respond to the user informatively in less than {MAX_CHARS} characters. "
        "Use the provided context history only for reference to maintain conversation context, and always focus on directly answering the user's current message.\n"
    )

    if context_history:
        structured_prompt += f"Context History:\n{context_history}\n"

    structured_prompt += f"Current Message: {new_prompt}\n"

    response = None
    model_used = None
    response_text = ""

    try:
        response = models["flash2.0"].generate_content(structured_prompt)
        response_text = f"Flash 2.0 Steve's Ghost says, \"{response.text.strip()}\""
        model_used = "flash-2.0"
    except Exception as e:
        if "429" in str(e): #Rate limit error
            try:
                response = models["pro"].generate_content(structured_prompt, max_output_tokens=MAX_CHARS)
                response_text = f"Pro Steve's Ghost says, \"{response.text.strip()}\""
                model_used = "pro"
            except Exception as e:
                if "429" in str(e):
                    try:
                        response = models["flash1.5"].generate_content(structured_prompt)
                        response_text = f"Flash 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                        model_used = "flash-1.5"
                    except Exception as e:
                        return f"Error with all models: {str(e)}", 500
                else:
                    return f"Error with Pro model: {str(e)}", 500
        else:
            return f"Error with Flash 2.0 model: {str(e)}", 500
    
    if not response:
        return "No response from the model.", 500

    if not code:
        code = generate_conversation_id()

    conversation_history[code] = (time.time(), response.text.strip())
    return f"{response_text} #{code}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
