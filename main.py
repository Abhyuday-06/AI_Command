from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure the Gemini API with your API key
genai.configure(api_key="AIzaSyD6wSDExmGOIIZ7dP-3wS2Vut7Xh1yHcAs")  # Replace with your Gemini API key

@app.route('/ai', methods=['GET'])
def ai_response():
    # Get the prompt from the querystring
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided."}), 400

    try:
        # Call Gemini API to generate content
        response = model.generate_content(prompt)
        return response.text  # Nightbot requires plain text, so return response as-is
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Use the port provided by Render or default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
