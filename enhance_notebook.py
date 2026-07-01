import json
from pathlib import Path


NOTEBOOK = Path("TicketRouter_Builder_Edition.ipynb")


def md(src: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in src.strip().split("\n")],
    }


def code(src: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in src.strip().split("\n")],
    }


custom_md = md(
    """
---
## Builder Edition: Ambiguous Smoke Tests

The original smoke test checks obvious cases. This section tests more realistic tickets where categories overlap, which is closer to production helpdesk routing.
"""
)

custom_code = code(
    """
# --- Builder smoke test: ambiguous real-world tickets -------------------------
custom_tickets = [
    ("My Outlook calendar invites are not showing up in Teams meetings.", "O365"),
    ("Please remove the old Dell workstation in room 204 from inventory and monitoring.", "EOL"),
    ("I can open the shared drive but not the marketing folder inside it.", "Fileservice"),
    ("New contractor needs access to the finance distribution group and shared apps.", "Active Directory"),
    ("The VPN client update failed and now the app will not launch.", "Software"),
]

print(f"{'Ticket (truncated)':<72} {'Expected':<20} {'Predicted':<20} {'Conf':>6}")
print("-" * 122)
for ticket, expected in custom_tickets:
    label, conf = classify(ticket)
    ok = "OK" if label == expected else "REVIEW"
    print(f"{ticket[:70]:<72} {expected:<20} {label:<20} {conf:>6.1%}  {ok}")
"""
)

gate_md = md(
    """
---
## Builder Edition: Confidence Gate for Human Review

A production router should not blindly auto-route every ticket. Low-confidence predictions are sent to human triage instead of being treated as final decisions.
"""
)

gate_code = code(
    """
# --- Production safety gate ---------------------------------------------------
def route_with_safety_gate(ticket_text: str, threshold: float = 0.70) -> dict:
    predicted_label, confidence = classify(ticket_text)

    if confidence < threshold:
        return {
            "predicted_label": predicted_label,
            "final_route": "Support general",
            "confidence": confidence,
            "action": "Human review required",
        }

    return {
        "predicted_label": predicted_label,
        "final_route": predicted_label,
        "confidence": confidence,
        "action": "Auto-route",
    }

safety_examples = [ticket for ticket, _ in custom_tickets]
for ticket in safety_examples:
    decision = route_with_safety_gate(ticket, threshold=0.70)
    print("Ticket:", ticket)
    print(decision)
    print()
"""
)

failure_md = md(
    """
---
## Builder Edition: Failure Mode Analysis

Use this section after reviewing the classification report and confusion matrix.

Likely routing risks:

- `O365` vs `Software`: Office apps are software, but Outlook, Teams, mailbox, calendar, SharePoint, and Office 365 issues should route to `O365`.
- `Fileservice` vs `Active Directory`: access-denied tickets can involve both file permissions and identity/group membership.
- `EOL` may have lower recall if the dataset has fewer lifecycle or decommissioning examples.
- `Support general` is useful as a fallback, but overuse reduces automation value.

Production mitigation:

- Keep a confidence threshold for auto-routing.
- Send ambiguous or low-confidence tickets to human triage.
- Monitor the confusion matrix monthly.
- Add new labeled examples from misrouted tickets before retraining.
"""
)

arch_md = md(
    """
---
## Builder Edition: Architecture Decision and Cost Analysis

This turns the notebook result into an engineering decision: why fine-tuning is the right tool, what it costs, and when this approach is worth deploying.
"""
)

arch_code = code(
    """
# --- Architecture decision table ---------------------------------------------
import pandas as pd

architecture_decision = pd.DataFrame([
    {"Approach": "API prompting", "Upfront": "Low", "Per-call": "High", "Right for this?": "No - expensive and less consistent at volume"},
    {"Approach": "RAG", "Upfront": "Low/Med", "Per-call": "Medium", "Right for this?": "No - routing is behavior, not knowledge lookup"},
    {"Approach": "Hosted fine-tune", "Upfront": "Medium", "Per-call": "Medium", "Right for this?": "Maybe - simple deployment, less local control"},
    {"Approach": "LoRA/QLoRA", "Upfront": "Low", "Per-call": "Low", "Right for this?": "Yes - small adapter learns routing behavior"},
    {"Approach": "Self-hosted full model", "Upfront": "High", "Per-call": "Lowest", "Right for this?": "Later - useful after traffic is proven"},
])
display(architecture_decision)

cost_breakdown = pd.DataFrame([
    {"Stage": "Data prep", "This project": "~2 hours human labeling/review time"},
    {"Stage": "Training", "This project": "Free Colab T4 for this run; low paid-GPU equivalent"},
    {"Stage": "Experiment runs", "This project": "1 baseline run + 1 LoRA fine-tune"},
    {"Stage": "Evaluation", "This project": "Included in notebook validation pass"},
    {"Stage": "Storage", "This project": "Small LoRA adapter plus merged model artifact"},
    {"Stage": "Serving", "This project": "Can run locally or on a small GPU endpoint"},
    {"Stage": "Monitoring", "This project": "Manual confusion-matrix review"},
    {"Stage": "Maintenance", "This project": "Retrain quarterly or after enough misroutes"},
])
display(cost_breakdown)

monthly_serving_cost = 20.00
api_cost_per_ticket = 0.002
break_even_tickets = monthly_serving_cost / api_cost_per_ticket
print(f"Example break-even: ${monthly_serving_cost:.0f}/month / ${api_cost_per_ticket:.3f} per ticket = {break_even_tickets:,.0f} tickets/month")
print("Privacy note: IT tickets can contain account names, access requests, device IDs, and internal systems. Local inference keeps that data inside the organization boundary.")
"""
)

model_card_md = md(
    """
---
## Builder Edition: Model Card

| Field | Value |
|---|---|
| Model name | TicketRouter v1.0 |
| Base model | Qwen/Qwen3-1.7B-Base |
| Fine-tuning method | LoRA adapter using LLaMA Factory |
| Task | 7-class IT support ticket routing |
| Labels | Support general, Fileservice, O365, EOL, Software, Active Directory, Computer-Services |
| Prompt format | ShareGPT-style system/user/assistant messages |
| Intended use | Internal first-pass routing to resolver queues |
| Not intended for | Customer-facing replies, final security approvals, or irreversible account actions |
| Safety layer | Low-confidence predictions route to Support general for human review |
| Known limitations | Ambiguous access tickets may confuse Fileservice and Active Directory; Office app issues may confuse O365 and Software; rare labels need more data |
| Rollback plan | Use baseline rules or human triage while collecting more labeled examples |
| Maintenance plan | Review misroutes monthly and retrain quarterly or after major workflow changes |
"""
)


nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
cells = nb["cells"]

for idx, new_cells in [
    (28, [arch_md, arch_code, model_card_md]),
    (25, [failure_md]),
    (19, [custom_md, custom_code, gate_md, gate_code]),
]:
    cells[idx:idx] = new_cells

NOTEBOOK.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Updated {NOTEBOOK} with {len(nb['cells'])} cells.")
