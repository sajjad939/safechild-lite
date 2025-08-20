const { OpenAI } = require('openai');

const api = new OpenAI({
  baseURL: 'https://api.aimlapi.com/v1',
  apiKey: '<YOUR_API_KEY>',
});

const main = async () => {
  const result = await api.chat.completions.create({
    model: 'openai/gpt-5-chat-latest',
    messages: [
      {
        role: 'system',
        content: 'You are an AI assistant who knows everything.',
      },
      {
        role: 'user',
        content: 'Tell me, why is the sky blue?'
      }
    ],
  });

  const message = result.choices[0].message.content;
  console.log(`Assistant: ${message}`);
};

main();
