"""import json
import os
import openai  # Install this library in requirements.txt

# Set up the OpenAI API key (replace with your own or use environment variables)
openai.api_key = os.getenv("OPENAI_API_KEY", "sk-Q94aZMdKc_YQy6ReeNWy_u0WQcANXtcg6rDfb2n9RpT3BlbkFJhEMkJmA2u5n0KUv2mZ4UztE8OhICyjj0gAgAp1AGYA")

def handler(request):
    # Get the query from the request
    query = request.args.get("query", "Hello! How can I assist you?")

    try:
        # Send the query to OpenAI
        response = openai.Completion.create(
            model="text-davinci-003",  # Adjust the model as needed
            prompt=query,
            max_tokens=100,
            temperature=0.7
        )
        result = response.choices[0].text.strip()

        # Return a JSON response
        return json.dumps({"response": result}), 200, {"Content-Type": "application/json"}

    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}
"""

from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Function executed successfully!")
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {e}".encode())
