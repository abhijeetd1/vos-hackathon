const express = require('express');
const { SpeechClient } = require('@google-cloud/speech');
const textToSpeech = require('@google-cloud/text-to-speech');

const app = express();
const cors = require('cors');
const fs = require('fs');
const bodyParser = require('body-parser');
const dialogflow = require('@google-cloud/dialogflow');
const uuid = require('uuid');

const corsOptions = {
    origin: 'http://localhost:3000', // Allow requests from this origin
    optionsSuccessStatus: 200 // Some legacy browsers choke on 204
  };

// Load the service account key JSON file
const keyFilename = '../key.json';
const dialogFlowKey = './dialogflow_creds.json'
const credentials = JSON.parse(fs.readFileSync(keyFilename, 'utf8'));
const dialogFlowCredentials = JSON.parse(fs.readFileSync(dialogFlowKey, 'utf8'));
// Create a client with explicit credentials
const client = new SpeechClient({
  credentials: {
    client_email: credentials.client_email,
    private_key: credentials.private_key,
  },
  projectId: credentials.project_id,
});

// Use CORS middleware
app.use(cors(corsOptions));
app.use(express.json());
app.use(bodyParser.json({ limit: '50mb' }));

const sessionClient = new dialogflow.SessionsClient({credentials: {
  client_email: dialogFlowCredentials.client_email,
  private_key: dialogFlowCredentials.private_key,
},
projectId: dialogFlowCredentials.project_id,});

// Google Cloud client setup
const textToSpeechClient = new textToSpeech.TextToSpeechClient({credentials: {
  client_email: dialogFlowCredentials.client_email,
  private_key: dialogFlowCredentials.private_key,
},
projectId: dialogFlowCredentials.project_id,});

// In-memory session store
const sessionStore = {};

// Function to detect intent and accumulate orders
async function detectIntentAndAccumulateOrders(projectId, languageCode, query, sessionId, isNewOrder) {
    const sessionPath = sessionClient.projectAgentSessionPath(projectId, sessionId);

    if (!sessionStore[sessionId]) {
        sessionStore[sessionId] = { items: [], total: null };
    }

    if (isNewOrder) {
      delete sessionStore[sessionId];
      sessionStore[sessionId] = { items: [], total: null };
    }

    const sessionData = sessionStore[sessionId];

    const request = {
        session: sessionPath,
        queryInput: {
            text: {
                text: query,
                languageCode: languageCode,
            },
        },
    };

    try {
        const responses = await sessionClient.detectIntent(request);
        const result = responses[0].queryResult;

        if (result.fulfillmentText.includes('error')) {
          return {
            fulfillmentText: result.fulfillmentText,
            foodItems: sessionData.items,
            total: sessionData.total, 
          }
        }
        // order_summary extraction
        if (responses[0].queryResult.webhookPayload) {
              const payload = responses[0].queryResult.webhookPayload
              if (payload.fields.order_summary.structValue) {
                let structValue = payload.fields.order_summary.structValue
                if (structValue.fields.total_amount) {
                  sessionData.total= structValue.fields.total_amount.numberValue
                }
                if (structValue.fields.items) {
                  let listValues = structValue.fields.items.listValue.values; 
                  let updatedItems = listValues.map((item) => {

                    return {
                      name: item.structValue.fields.name.stringValue, 
                      price: item.structValue.fields.item_total.numberValue, 
                      quantity: item.structValue.fields.quantity.numberValue, 
                      size: item.structValue.fields.size ? item.structValue.fields.size.stringValue : null,
                      customizations: item.structValue.fields.customizations.listValue.values.map((custom) => {
                        return custom.stringValue
                      })
                    }
                   
                  })
                  sessionData.items = updatedItems;
                }
              }
          }

        return {
            fulfillmentText: result.fulfillmentText,
            foodItems: sessionData.items,
            total: sessionData.total, 
        };
        
    } catch (error) {
        console.error('ERROR:', error);
        throw error;
    }
}

// API endpoint to extract products 
app.post('/detect-intent', async (req, res) => {
    const { query, sessionId, isNewOrder} = req.body;
    const projectId = 'burner-abhdey0'; 
    const languageCode = 'en'; 

    try {
        const response = await detectIntentAndAccumulateOrders(projectId, languageCode, query, sessionId, isNewOrder);
        res.json(response);
    } catch (error) {
        res.status(500).send('Error processing request');
    }
});

// API endpoint to transcribe audio
app.post('/transcribe', async (req, res) => {
  try {
    const audioBase64 = req.body.audio;
    const audioBytes = Buffer.from(audioBase64, 'base64');

    const request = {
      audio: {
        content: audioBytes.toString('base64'),
      },
      config: {
        encoding: 'WEBM_OPUS',
        sampleRateHertz: 48000,
        languageCode: 'en-US',
      },
    };

    const [response] = await client.recognize(request);
    const transcription = response.results
      .map(result => result.alternatives[0].transcript)
      .join('\n');

    res.json({ transcription });
  } catch (error) {
    console.error('Error transcribing audio:', error);
    res.status(500).send('Error transcribing audio');
  }
});

app.post('/synthesize', async (req, res) => {
  const text = req.body.text;

  const request = {
    input: { text: text },
    voice: { languageCode: 'en-US', ssmlGender: 'NEUTRAL' },
    audioConfig: { audioEncoding: 'MP3' },
  };

  try {
    const [response] = await textToSpeechClient.synthesizeSpeech(request);
    res.set('Content-Type', 'audio/mp3');
    res.send(response.audioContent);
  } catch (error) {
    console.log(error)
    res.status(500).send('Error synthesizing speech');
  }
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
