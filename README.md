# Project Name

This project is a Flask-based web application that provides an AI-powered chat service. It uses Google's Gemini models to generate responses and can fetch real-time data from the internet to answer questions.

## Features

- **Conversational AI:** The application can engage in conversations with users, remembering the context of the conversation.
- **Real-time Data:** The application can fetch real-time data from the internet to answer questions about current events.
- **Multiple AI Models:** The application uses a variety of Gemini models to generate responses, with a fallback system in case of errors.
- **Conversation History:** The application stores conversation history for a limited time, allowing users to continue previous conversations.

## Dependencies

The following dependencies are required to run the application:

- Flask
- google-generativeai
- requests
- numpy
- openai==0.28
- sentence-transformers

These dependencies can be installed using the `requirements.txt` file.

## Installation

To install the dependencies, run the following command:

```
pip install -r requirements.txt
```

## Running the Application

To run the application, you need to set the following environment variables:

- `GEMINI_API_KEY`: Your API key for the Gemini API.
- `GOOGLE_API_KEY`: Your API key for the Google Custom Search JSON API.
- `GOOGLE_CSE_ID`: Your Custom Search Engine ID.

Once you have set the environment variables, you can run the application with the following command:

```
python main.py
```

The application will be available at `http://localhost:8080`.

## API Endpoint

The application has a single API endpoint: `/ai`. This endpoint accepts a `GET` request with the following query parameters:

- `prompt`: The user's prompt.

The response will be a string containing the AI's response.

### Example

To get a response from the AI, you can send a `GET` request to the following URL:

```
http://localhost:8080/ai?prompt=Hello
```

The response will be a string similar to the following:

```
Pro 2.5 Steve's Ghost says, "Hello there! How can I help you today?" #abc
```

The `#abc` at the end of the response is a conversation ID. You can use this ID to continue the conversation by starting your next prompt with `#abc`. For example:

```
http://localhost:8080/ai?prompt=%23abc%20What%20is%20the%20weather%20like%20today%3F
```
