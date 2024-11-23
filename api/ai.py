import json
import os
import openai

# Make sure the OpenAI API key is passed correctly through environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

def handler(request):
    # Get the query parameter (you can pass it through the URL like /api/ai?query=your_query)
    query = request.args.get("query", "Hello! How can I assist you?")

    try:
        # Send the query to OpenAI API
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=query,
            max_tokens=100,
            temperature=0.7
        )
        result = response.choices[0].text.strip()

        # Return the result as a JSON response
        return {
            "statusCode": 200,
            "body": json.dumps({"response": result}),
            "headers": {"Content-Type": "application/json"}
        }

    except Exception as e:
        # Catch and return any errors
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
