# TicketRouter Ops Console

TicketRouter is a confidence-gated IT support ticket routing project built around a fine-tuned Qwen3-1.7B model with a LoRA adapter.

The selected model is **Run 2**, which reached **77.8% validation accuracy**, improving over the 24.8% baseline by **+53.0 percentage points**.

## Why This Is More Than A Notebook

The project includes a small Streamlit product demo that presents the model as an internal helpdesk routing console:

- Single-ticket routing
- Batch ticket routing
- Confidence-based human review gate
- Run comparison dashboard
- Failure analysis
- Model card

The deployed UI defaults to a lightweight routing simulator so it can run reliably on Streamlit Cloud without a GPU. The real model evidence comes from the notebook experiments and the merged Hugging Face model artifact.

## Production-Style Cloud Run Deployment

The repo also includes a deployable inference API in `cloudrun/`. This separates the public Streamlit ops console from the heavier model-serving layer:

```text
Streamlit UI -> Cloud Run FastAPI endpoint -> TicketRouter-1.7B model on Hugging Face
```

The Cloud Run service exposes:

- `GET /health` for service status and GPU availability
- `POST /route` for model-backed ticket routing
- confidence-gated human review behavior for ambiguous tickets

Deploy the API only when you are ready to test or record a demo, then delete it to control cost:

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

After deployment, set `TICKETROUTER_API_URL` in Streamlit Cloud secrets to the Cloud Run URL and select **Cloud Run API** in the app sidebar.

Capture for resume/demo proof:

- Cloud Run service page
- `/health` response
- one `/route` response
- Streamlit UI using Cloud Run API mode
- Cloud Run request logs

Shutdown command:

```bash
gcloud run services delete ticketrouter-api --region us-central1
```

## Experiment Summary

| Metric | Run 1 | Run 2 | Run 3 | Run 4 |
|---|---:|---:|---:|---:|
| Accuracy | 73.5% | **77.8%** | 74.4% | 74.4% |
| Active Directory F1 | 0.308 | **0.471** | 0.308 | 0.267 |
| Software F1 | 0.600 | 0.522 | **0.609** | 0.583 |
| Macro F1 | 0.699 | **0.753** | 0.717 | 0.718 |

Run 2 was selected because it produced the best overall accuracy, best macro F1, and best Active Directory F1. Run 3 and Run 4 showed that the remaining Active Directory weakness is a data-quality problem, not simply an epoch-count problem.

## Run The Streamlit Demo

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deployment Note

The merged Run 2 model is hosted on Hugging Face as `Neog007/TicketRouter-1.7B`. The repository contains a valid Qwen3 config and merged `model.safetensors` artifact.

Directly loading a 1.7B parameter model inside free Streamlit Cloud is resource intensive and may exceed the available memory/CPU budget. For a reliable public demo, `app.py` defaults to **Stable demo mode**, which mirrors the product workflow:

- single-ticket routing
- batch routing
- confidence-style human review gate
- model card and experiment evidence

The sidebar also includes **Try Hugging Face model** for environments that can load the full model.

## Project Files

- `TicketRouter_Builder_Edition.ipynb` - main builder notebook
- `TicketRouter_Run2_Targeted_Accuracy.ipynb` - selected production candidate
- `TicketRouter_Run3_Failure_Driven.ipynb` - boundary-data experiment
- `TicketRouter_Run4_Failure_Driven_4Epochs.ipynb` - controlled epoch-count experiment
- `app.py` - Streamlit Cloud deployment app with stable demo mode and optional Hugging Face model loading
- `streamlit_app.py` - lightweight local ops-console demo
- `cloudrun/` - FastAPI model-serving backend for Cloud Run GPU deployment

## Final Decision

**Selected model: Run 2**

Run 2 is the production candidate because it had the strongest validation performance and the best balance across routing classes. The remaining improvement path is to collect better real-world Active Directory and Software tickets before retraining.
