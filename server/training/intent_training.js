const dialogflow = require('@google-cloud/dialogflow');
const fs = require('fs');
const path = require('path');

// Path to your JSON file containing training phrases
const trainingPhrasesFilePath = path.join(__dirname, 'trainingPhrasesCombined.json');

// Read the training phrases from the file
const trainingPhrasesData = JSON.parse(fs.readFileSync(trainingPhrasesFilePath, 'utf8'));

// Dialogflow project ID
const projectId = 'burner-abhdey0';

// Create a new client
const intentsClient = new dialogflow.IntentsClient();

async function updateIntent(intentId, trainingPhrases) {
  const intentPath = intentsClient.projectAgentIntentPath(projectId, intentId);

  // Fetch the existing intent
  const [intent] = await intentsClient.getIntent({ name: intentPath });

  // Map training phrases to Dialogflow format, handling entities
  const newTrainingPhrases = trainingPhrases.map(phrase => {
    const parts = [];
    const regex = /@([a-zA-Z0-9_.-]+):'([^']+)'/g;
    let match;
    let lastIndex = 0;

    while ((match = regex.exec(phrase)) !== null) {
      // Add text before the entity
      if (match.index > lastIndex) {
        parts.push({ text: phrase.substring(lastIndex, match.index) });
      }
      // Add the entity
      parts.push({
        text: match[2],
        entityType: `@${match[1]}`,
        alias: match[1].replace('sys.', ''), // Remove 'sys.' prefix for alias
        userDefined: !match[1].startsWith('sys.')
      });
      lastIndex = regex.lastIndex;
    }

    // Add any remaining text after the last entity
    if (lastIndex < phrase.length) {
      parts.push({ text: phrase.substring(lastIndex) });
    }

    return { type: 'EXAMPLE', parts };
  });

  // Update the intent's training phrases
  intent.trainingPhrases = newTrainingPhrases;

  // Update the intent in Dialogflow
  const updateMask = { paths: ['training_phrases'] };
  const request = { intent, updateMask };

  await intentsClient.updateIntent(request);
  console.log(`Intent ${intentId} updated successfully.`);
}

// Iterate over each intent in the JSON file and update it
for (const [intentId, phrases] of Object.entries(trainingPhrasesData)) {
  updateIntent(intentId, phrases).catch(console.error);
}

// listIntentsAndUUIDs(projectId)

async function listIntentsAndUUIDs(projectId) {
  const projectAgentPath = intentsClient.projectAgentPath(projectId);

  try {
    const [intents] = await intentsClient.listIntents({ parent: projectAgentPath });
    intents.forEach(intent => {
      // The name property contains the full path, including the UUID
      const intentName = intent.name;
      const intentUUID = intentName.split('/').pop(); // Extract the UUID from the full path
      console.log(`Intent name: ${intent.displayName}, UUID: ${intentUUID}`);
    });
    console.log('Intents listed successfully.');
  } catch (error) {
    console.error('Error listing intents:', error);
  }
}