from flask import Flask, request, jsonify
import google.generativeai as genai
import os
import time
from threading import Timer

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=api_key)

flash2_0_model = genai.GenerativeModel("gemini-2.0-flash-exp")
pro_model = genai.GenerativeModel("gemini-1.5-pro-002")
flash1_5_model = genai.GenerativeModel("gemini-1.5-flash-8b-latest")

conversation_history = {}
EXPIRATION_TIME = 3 * 60 * 60  # 3 hours

def clean_up_history():
    current_time = time.time()
    expired_keys = [key for key, (timestamp, _) in conversation_history.items() if current_time - timestamp > EXPIRATION_TIME]
    for key in expired_keys:
        del conversation_history[key]

def schedule_cleanup():
    Timer(600, clean_up_history).start()

schedule_cleanup()

@app.route('/ai', methods=['GET'])
def ai_response():
    global conversation_history
    raw_prompt = request.args.get('prompt', '')
    if not raw_prompt:
        return jsonify({"error": "No prompt provided."}), 400

    if raw_prompt.startswith('#'):
        parts = raw_prompt.split(' ', 1)
        code = parts[0][1:]  # Extract the code after '#'
        new_prompt = parts[1].strip() if len(parts) > 1 else ''
    else:
        code = None
        new_prompt = raw_prompt.strip()

    context = None
    if code and code in conversation_history:
        _, last_response = conversation_history[code]
        context = last_response

    structured_prompt = (
        "Respond to the users informatically in less than 350 characters. "
        "Use the provided context only for reference, and always focus on answering the user's current message.\n"
    )

    if context:
        structured_prompt += f"Context: {context}\n"

    structured_prompt += (
        "Current Message: {new_prompt}\n"
    ).format(new_prompt=new_prompt)

    try:
        response = flash2_0_model.generate_content(structured_prompt)
        response_text = f"Flash 2.0 Steve's Ghost says, \"{response.text.strip()}\""
        model_used = "flash-2.0"
    except Exception as e:
        try:
            response = pro_model.generate_content(structured_prompt)
            response_text = f"Pro Steve's Ghost says, \"{response.text.strip()}\""
            model_used = "pro"
        except Exception as pro_error:
            try:
                response = flash1_5_model.generate_content(structured_prompt)
                response_text = f"Flash 1.5 Steve's Ghost says, \"{response.text.strip()}\""
                model_used = "flash-1.5"
            except Exception as flash_error:
                return jsonify({"error": "All models failed.", "details": str(flash_error)}), 500

    if not code or code not in conversation_history:
        code = ''.join([chr(ord('a') + (int(time.time()) + i) % 26) for i in range(3)])

    conversation_history[code] = (time.time(), response.text.strip())
    return jsonify({"response": response_text, "code": code, "model_used": model_used})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
