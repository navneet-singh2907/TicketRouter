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

## Build Locally First

Build the container from the repo root:

```bash
docker build -t ticketrouter-api:local ./cloudrun
```

Run the API locally:

```bash
docker run --rm -p 8080:8080 \
  -e MODEL_ID=Neog007/TicketRouter-1.7B \
  -e REVIEW_THRESHOLD=0.70 \
  ticketrouter-api:local
```

In another terminal:

```bash
curl http://localhost:8080/health
```

The first `/route` request will download and load the model, so it can take a while:

```bash
curl -X POST http://localhost:8080/route \
  -H "Content-Type: application/json" \
  -d "{\"ticket\":\"My Outlook calendar is not syncing with Teams.\"}"
```

On a normal laptop, local CPU inference may be very slow or fail due memory. The local Docker test is mainly to prove the container starts; Cloud Run GPU is the real serving target.

## Deploy With Source Build

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

## Deploy A Prebuilt Image

If you want the fully old-fashioned path, build and push the image yourself, then deploy the image:

```bash
gcloud artifacts repositories create ticketrouter \
  --repository-format=docker \
  --location=us-central1

gcloud auth configure-docker us-central1-docker.pkg.dev

docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ticketrouter/ticketrouter-api:run2 ./cloudrun

docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ticketrouter/ticketrouter-api:run2

gcloud run deploy ticketrouter-api \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ticketrouter/ticketrouter-api:run2 \
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
