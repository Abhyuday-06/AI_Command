from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import random
import string
import time
from threading import Thread

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=api_key)

pro_model = genai.GenerativeModel("gemini-1.5-pro")
flash_model = genai.GenerativeModel("gemini-1.5-flash")

conversation_contexts = {}  # Stores context as {code: {"timestamp": <time>, "context": <context>}}


def generate_code():
    """Generate a unique 3-letter alphanumeric code."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=3))


def cleanup_old_contexts():
    """Remove conversation contexts older than 3 hours."""
    while True:
        current_time = time.time()
        to_delete = [
            code for code, data in conversation_contexts.items()
            if current_time - data['timestamp'] > 3 * 60 * 60  
        ]
        for code in to_delete:
            del conversation_contexts[code]
        time.sleep(60)  


@app.route('/ai', methods=['GET'])
def ai_response():
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided."}), 400

    if prompt.startswith("#"):
        code, _, new_prompt = prompt.partition(" ")
        code = code[1:]  
        if code in conversation_contexts:
            # Retrieve and prepend the context
            previous_context = conversation_contexts[code]["context"]
            prompt = previous_context + " " + new_prompt.strip()
        else:
            return f"Error: Conversation with code #{code} not found.", 404

    else:
        code = generate_code()

    try:
        response = pro_model.generate_content(prompt + " in 50 words max.")
        answer = response.text.strip()
        message = f"Pro Steve's Ghost says, \"{answer}\" #{code}"
    except Exception as e:
        error_message = str(e)
        if "429" in error_message and "Resource has been exhausted" in error_message:
            try:
                flash_response = flash_model.generate_content(prompt + " in 50 words max.")
                answer = flash_response.text.strip()
                message = f"Flash Steve's Ghost says, \"{answer}\" #{code}"
            except Exception as flash_error:
                return f"Error (Flash Model): {str(flash_error)}", 500
        else:
            return f"Error: {error_message}", 500

    conversation_contexts[code] = {
        "timestamp": time.time(),
        "context": answer  # Save only the answer for context, not the full prompt
    }

    return message


if __name__ == '__main__':
    cleanup_thread = Thread(target=cleanup_old_contexts, daemon=True)
    cleanup_thread.start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
