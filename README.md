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

The UI intentionally uses a lightweight routing simulator so it can run locally without a GPU. The real model evidence comes from the notebook experiments.

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

## Project Files

- `TicketRouter_Builder_Edition.ipynb` - main builder notebook
- `TicketRouter_Run2_Targeted_Accuracy.ipynb` - selected production candidate
- `TicketRouter_Run3_Failure_Driven.ipynb` - boundary-data experiment
- `TicketRouter_Run4_Failure_Driven_4Epochs.ipynb` - controlled epoch-count experiment
- `app.py` - Streamlit Cloud deployment app using `Neog007/TicketRouter-1.7B`
- `streamlit_app.py` - lightweight local ops-console demo

## Final Decision

**Selected model: Run 2**

Run 2 is the production candidate because it had the strongest validation performance and the best balance across routing classes. The remaining improvement path is to collect better real-world Active Directory and Software tickets before retraining.
