from flask import Flask, request
import google.generativeai as genai

app = Flask(__name__)

# Configure the Gemini API with your API key
genai.configure(api_key="AIzaSyD6wSDExmGOIIZ7dP-3wS2Vut7Xh1yHcAs")  # Replace with your Gemini API key

@app.route('/ai', methods=['GET'])
def ai_response():
    prompt = request.args.get('prompt')  # Get the prompt from the querystring
    if not prompt:
        return "No prompt provided."

    try:
        # Call Gemini API to generate content
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
