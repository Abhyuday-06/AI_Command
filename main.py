from flask import Flask, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Configure the Gemini API with your API key (securely fetched from environment variables)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")
genai.configure(api_key=api_key)

# Initialize the models
pro_model = genai.GenerativeModel("gemini-1.5-pro")
flash_model = genai.GenerativeModel("gemini-flash")

@app.route('/ai', methods=['GET'])
def ai_response():
    # Get the prompt from the querystring
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided."}), 400

    try:
        # Try using the Pro model
        response = pro_model.generate_content(prompt + " in 50 words max.")
        return f"Pro Steve's Ghost says, \"{response.text.strip()}\""
    except Exception as e:
        # Check if the error is due to quota exhaustion
        error_message = str(e)
        if "429" in error_message and "Resource has been exhausted" in error_message:
            try:
                # Fallback to the Flash model
                flash_response = flash_model.generate_content(prompt + " in 50 words max.")
                return f"Flash Steve's Ghost says, \"{flash_response.text.strip()}\""
            except Exception as flash_error:
                # Handle any errors from the Flash model
                return f"Error (Flash Model): {str(flash_error)}", 500
        else:
            # For any other errors, return the original error message
            return f"Error: {error_message}", 500

if __name__ == '__main__':
    # Use the port provided by Render or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
