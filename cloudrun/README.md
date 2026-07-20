# TicketRouter Cloud Run API

This folder packages the selected Run 2 model as a production-style inference API.

## Endpoints

- `GET /health` - service health, model id, GPU availability, and lazy-load status
- `POST /route` - route one IT support ticket

Example request:

```bash
curl -X POST "$TICKETROUTER_API_URL/route" \
  -H "Content-Type: application/json" \
  -d "{\"ticket\":\"My Outlook calendar is not syncing with Teams.\"}"
```

Example response:

```json
{
  "predicted_label": "O365",
  "final_route": "O365",
  "confidence": 0.89,
  "action": "Auto-route",
  "model_id": "Neog007/TicketRouter-1.7B"
}
```

## Deploy To Cloud Run GPU

Use GPU only when you are ready to capture a demo or run real tests. Keep the service cost-limited with `min-instances=0` and `max-instances=1`.

```bash
gcloud run deploy ticketrouter-api \
  --source cloudrun \
  --region us-central1 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --cpu 4 \
  --memory 16Gi \
  --min-instances 0 \
  --max-instances 1 \
  --allow-unauthenticated \
  --set-env-vars MODEL_ID=Neog007/TicketRouter-1.7B,REVIEW_THRESHOLD=0.70
```

If the Hugging Face model ever requires authentication, add `HF_TOKEN` as a Cloud Run secret instead of hard-coding it.

## Test After Deploy

```bash
export TICKETROUTER_API_URL="https://YOUR-CLOUD-RUN-URL"

curl "$TICKETROUTER_API_URL/health"

curl -X POST "$TICKETROUTER_API_URL/route" \
  -H "Content-Type: application/json" \
  -d "{\"ticket\":\"Please create an Active Directory user account for a new contractor.\"}"
```

## Shut Down After Recording

Delete the service when you are done capturing screenshots or video:

```bash
gcloud run services delete ticketrouter-api --region us-central1
```

For resume proof, capture the Cloud Run service page, `/health`, one `/route` response, and request logs.
