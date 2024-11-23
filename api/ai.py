import json
import os
import openai

# Make sure the OpenAI API key is passed correctly through environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key is missing!")
openai.api_key = openai_api_key

def handler(request):
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="Say hello!",
            max_tokens=10
        )
        return json.dumps({"response": response.choices[0].text.strip()}), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}
