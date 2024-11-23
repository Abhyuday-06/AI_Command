import fetch from "node-fetch";

export default async function handler(req, res) {
  const query = req.query.query || "Hello! How can I assist you?";
  
  // Replace with your AI API endpoint and key
  const response = await fetch("https://api.openai.com/v1/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer YOUR_OPENAI_API_KEY`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "text-davinci-003", // Replace with your AI model
      prompt: query,
      max_tokens: 100,
    }),
  });

  const data = await response.json();

  res.status(200).json({ response: data.choices[0].text.trim() });
}
