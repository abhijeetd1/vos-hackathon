# Voice Order System Fulfillment Service

This repository contains the fulfillment service for a voice ordering system built with Dialogflow ES and Google Cloud Functions. The service handles order management, customizations, and integrates with Firestore for data persistence.

## Prerequisites

- Python 3.8 or higher
- Google Cloud SDK
- Firebase CLI
- Access to Google Cloud Platform project
- Access to Firebase project

## Project Structure

```
.
├── README.md
├── main.py                 # Main fulfillment service code
├── requirements.txt        # Python dependencies
├── firebase-key.json      # Firebase service account key 
├── firestore/             # Firestore collection structures
│   ├── menu_items.json    
│   ├── orders.json
│   └── configs.json
└── dialogflow/            # Dialogflow backup
    ├── intents/
    └── entities/
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up Firebase credentials:
   - Generate a new service account key from Firebase Console
   - Save it as `firebase-key.json` in the project root
   - Add `firebase-key.json` to .gitignore

## Local Development

1. Install the Functions Framework:
   ```bash
   pip install functions-framework
   ```

2. Run the function locally:
   ```bash
   functions-framework --target=handle_request --debug
   ```

3. The function will be available at `http://localhost:8080`

## Deployment

1. Make sure you have the Google Cloud SDK installed and initialized:
   ```bash
   gcloud init
   ```

2. Set your project ID:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

3. Deploy the function:
   ```bash
   gcloud functions deploy voice_order_fulfillment \
     --runtime python39 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point handle_request \
     --region YOUR_REGION
   ```

4. After deployment, update the webhook URL in Dialogflow ES console with the function's URL

## Environment Variables

The following environment variables need to be set in the Google Cloud Function:

- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `FIRESTORE_DATABASE`: Name of your Firestore database (default: 'mcd-vos')

## Firestore Collections

The service requires the following Firestore collections:

1. `menu_items`: Contains available food and drink items
2. `orders`: Stores completed orders
3. `configs`: Contains configuration settings like order limits

Refer to the `firestore/` directory for collection structures.

## Testing

1. Use the local development server to test the fulfillment service
2. Send POST requests to the endpoint with Dialogflow webhook format
3. Monitor the logs for debugging information

## Production Considerations

1. Enable appropriate IAM roles for the service account
2. Set up monitoring and logging
3. Configure appropriate security rules for Firestore
4. Implement rate limiting and quotas
5. Set up proper error tracking

