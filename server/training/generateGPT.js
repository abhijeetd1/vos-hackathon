const { OpenAI } = require("openai");

// OpenAI API key setup (replace 'your-api-key' with your actual API key)
const openai = new OpenAI({
  apiKey: 'valid-openai-key',
});

// Sample training data
const trainingData = [
  "can i get a @food-item:'mcchicken', @sys.number:'one' medium @food-item:'fries' and @drink-size:'small' drink",
];

// Function to generate similar phrases using OpenAI API
async function generateSimilarPhrases(phrase) {
  try {
    const response = await openai.chat.completions.create({
      model: "gpt-3.5-turbo",
      messages: [
        { role: "system", content: "You are a helpful assistant that generates similar phrases." },
        { role: "user", content: `Generate similar phrases for: ${phrase}` }
      ],
      max_tokens: 1,
      temperature: 0.5
    });

    return response.data.choices.map(choice => choice.message.content.trim());
  } catch (error) {
    console.error("Error generating phrases:", error);
    return [];
  }
}

// Generate and print similar phrases for each training phrase
(async () => {
  for (const phrase of trainingData) {
    console.log(`Original: ${phrase}`);
    const similarPhrases = await generateSimilarPhrases(phrase);
    similarPhrases.forEach(sp => console.log(`Similar: ${sp}`));
    console.log("\n");
  }
})();