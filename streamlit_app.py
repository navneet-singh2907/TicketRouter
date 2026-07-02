from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
import streamlit as st


LABELS = [
    "Support general",
    "Fileservice",
    "O365",
    "EOL",
    "Software",
    "Active Directory",
    "Computer-Services",
]

RUN_RESULTS = pd.DataFrame(
    [
        {"Run": "Baseline", "Accuracy": 0.248, "Macro F1": 0.078, "Active Directory F1": 0.000, "Software F1": 0.000},
        {"Run": "Run 1", "Accuracy": 0.735, "Macro F1": 0.699, "Active Directory F1": 0.308, "Software F1": 0.600},
        {"Run": "Run 2", "Accuracy": 0.778, "Macro F1": 0.753, "Active Directory F1": 0.471, "Software F1": 0.522},
        {"Run": "Run 3", "Accuracy": 0.744, "Macro F1": 0.717, "Active Directory F1": 0.308, "Software F1": 0.609},
        {"Run": "Run 4", "Accuracy": 0.744, "Macro F1": 0.718, "Active Directory F1": 0.267, "Software F1": 0.583},
    ]
)

RUN2_CLASS_RESULTS = pd.DataFrame(
    [
        {"Class": "Support general", "Precision": 0.697, "Recall": 0.767, "F1": 0.730, "Support": 30},
        {"Class": "Fileservice", "Precision": 0.958, "Recall": 0.821, "F1": 0.885, "Support": 28},
        {"Class": "O365", "Precision": 0.800, "Recall": 0.889, "F1": 0.842, "Support": 18},
        {"Class": "EOL", "Precision": 1.000, "Recall": 1.000, "F1": 1.000, "Support": 12},
        {"Class": "Software", "Precision": 0.545, "Recall": 0.500, "F1": 0.522, "Support": 12},
        {"Class": "Active Directory", "Precision": 0.500, "Recall": 0.444, "F1": 0.471, "Support": 9},
        {"Class": "Computer-Services", "Precision": 0.778, "Recall": 0.875, "F1": 0.824, "Support": 8},
    ]
)

SAMPLE_TICKETS = [
    "My Outlook calendar invites are not showing up in Teams meetings.",
    "Please create an Active Directory user account and assign standard finance security groups.",
    "I can open the shared drive but not the marketing folder inside it.",
    "Please remove the old Dell workstation in room 204 from inventory and monitoring.",
    "The VPN client update failed and now the app will not launch.",
]


@dataclass(frozen=True)
class RouteDecision:
    predicted_label: str
    confidence: float
    final_route: str
    action: str
    evidence: str


def keyword_score(text: str, patterns: dict[str, list[str]]) -> dict[str, int]:
    normalized = text.lower()
    scores: dict[str, int] = {}
    for label, terms in patterns.items():
        scores[label] = sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", normalized))
    return scores


def predict_ticket(ticket: str, threshold: float) -> RouteDecision:
    patterns = {
        "O365": [
            "outlook",
            "teams",
            "sharepoint",
            "onedrive",
            "mailbox",
            "calendar",
            "microsoft 365",
            "office 365",
            "excel online",
            "shared mailbox",
        ],
        "Active Directory": [
            "active directory",
            "ad",
            "domain account",
            "security group",
            "distribution group",
            "group membership",
            "locked out",
            "unlock",
            "password reset",
            "mfa",
            "provision",
        ],
        "Fileservice": [
            "shared drive",
            "network folder",
            "file share",
            "folder",
            "drive",
            "deleted file",
            "restore",
            "permissions",
        ],
        "EOL": [
            "decommission",
            "retire",
            "remove",
            "old workstation",
            "inventory",
            "monitoring",
            "end of life",
            "eol",
        ],
        "Software": [
            "install",
            "installation",
            "software",
            "app",
            "application",
            "vpn client",
            "adobe",
            "acrobat",
            "zoom",
            "license",
            "crashes",
            "update failed",
            "error code",
        ],
        "Computer-Services": [
            "laptop",
            "workstation",
            "printer",
            "hardware",
            "device",
            "monitor",
            "keyboard",
            "dock",
            "imaging",
        ],
    }

    scores = keyword_score(ticket, patterns)
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]

    if best_score == 0:
        best_label = "Support general"
        confidence = 0.42
        evidence = "No strong resolver-queue keywords found."
    else:
        total = sum(scores.values())
        margin = best_score - sorted(scores.values(), reverse=True)[1]
        confidence = min(0.98, 0.45 + (best_score / max(total, 1)) * 0.35 + margin * 0.08)
        evidence_terms = [term for term in patterns[best_label] if re.search(rf"\b{re.escape(term)}\b", ticket.lower())]
        evidence = f"Matched {best_label} signals: {', '.join(evidence_terms[:4])}."

    ambiguous_access = any(
        phrase in ticket.lower()
        for phrase in ["access", "permission", "group", "shared", "contractor", "new employee", "new hire"]
    )
    if best_label in {"Active Directory", "Fileservice", "O365"} and ambiguous_access:
        confidence = min(confidence, 0.82)
        evidence += " Access wording overlaps with other queues, so review risk is elevated."

    if confidence < threshold:
        return RouteDecision(
            predicted_label=best_label,
            confidence=confidence,
            final_route="Support general",
            action="Human review required",
            evidence=evidence,
        )

    return RouteDecision(
        predicted_label=best_label,
        confidence=confidence,
        final_route=best_label,
        action="Auto-route",
        evidence=evidence,
    )


def route_many(raw_text: str, threshold: float) -> pd.DataFrame:
    tickets = [line.strip() for line in raw_text.splitlines() if line.strip()]
    rows = []
    for ticket in tickets:
        decision = predict_ticket(ticket, threshold)
        rows.append(
            {
                "Ticket": ticket,
                "Predicted label": decision.predicted_label,
                "Confidence": f"{decision.confidence:.1%}",
                "Final route": decision.final_route,
                "Action": decision.action,
            }
        )
    return pd.DataFrame(rows)


st.set_page_config(page_title="TicketRouter Ops Console", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; max-width: 1180px; }
    [data-testid="stMetricValue"] { font-size: 1.7rem; }
    .decision-box {
        border: 1px solid #d8dee9;
        border-radius: 8px;
        padding: 1rem;
        background: #f8fafc;
    }
    .small-muted { color: #64748b; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("TicketRouter Ops Console")
st.caption("Confidence-gated IT ticket routing demo built around the selected Run 2 Qwen3 + LoRA experiment.")

with st.sidebar:
    st.header("Model Selection")
    st.success("Selected model: Run 2")
    threshold = st.slider("Human review threshold", min_value=0.40, max_value=0.95, value=0.70, step=0.05)
    st.divider()
    st.write("Run 2 was selected because it had the best accuracy, macro F1, and Active Directory F1 across four controlled runs.")
    st.dataframe(
        RUN_RESULTS.set_index("Run").style.format(
            {"Accuracy": "{:.1%}", "Macro F1": "{:.3f}", "Active Directory F1": "{:.3f}", "Software F1": "{:.3f}"}
        ),
        width="stretch",
    )

overview, single, batch, analysis, model_card = st.tabs(
    ["Overview", "Single Ticket", "Batch Routing", "Failure Analysis", "Model Card"]
)

with overview:
    st.subheader("Production Candidate")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baseline accuracy", "24.8%")
    c2.metric("Run 2 accuracy", "77.8%", "+53.0 pts")
    c3.metric("Macro F1", "0.753")
    c4.metric("Human review gate", f"{threshold:.0%}")

    st.markdown("#### Experiment Results")
    chart_data = RUN_RESULTS[RUN_RESULTS["Run"] != "Baseline"].set_index("Run")[["Accuracy", "Macro F1"]]
    st.bar_chart(chart_data)

    st.markdown("#### Run 2 Per-Class Evaluation")
    st.dataframe(
        RUN2_CLASS_RESULTS.style.format({"Precision": "{:.3f}", "Recall": "{:.3f}", "F1": "{:.3f}"}),
        width="stretch",
        hide_index=True,
    )

with single:
    st.subheader("Route One Ticket")
    example = st.selectbox("Load example", ["Custom"] + SAMPLE_TICKETS)
    default_ticket = "" if example == "Custom" else example
    ticket_text = st.text_area("Support ticket", value=default_ticket, height=150)

    if st.button("Route ticket", type="primary", width="content"):
        if not ticket_text.strip():
            st.warning("Enter a ticket before routing.")
        else:
            decision = predict_ticket(ticket_text, threshold)
            left, right = st.columns([1, 1])
            with left:
                st.metric("Predicted label", decision.predicted_label)
                st.metric("Confidence", f"{decision.confidence:.1%}")
            with right:
                st.metric("Final route", decision.final_route)
                st.metric("Action", decision.action)
            st.info(decision.evidence)

with batch:
    st.subheader("Batch Routing")
    st.caption("Paste one ticket per line. This mimics a helpdesk triage queue.")
    batch_text = st.text_area("Tickets", value="\n".join(SAMPLE_TICKETS), height=190)
    if st.button("Route batch", type="primary"):
        routed = route_many(batch_text, threshold)
        if routed.empty:
            st.warning("Paste at least one ticket.")
        else:
            st.dataframe(routed, width="stretch", hide_index=True)
            action_counts = routed["Action"].value_counts().rename_axis("Action").reset_index(name="Count")
            st.bar_chart(action_counts.set_index("Action"))

with analysis:
    st.subheader("Failure Analysis")
    st.markdown(
        """
        Run 2 is the production candidate, but the confusion matrix showed one important risk:

        - Active Directory remained the weakest class.
        - Ambiguous access tickets can be confused with Support general, O365, or Fileservice.
        - Run 3 and Run 4 proved the regression was caused by boundary-example data quality, not epoch count.
        - The next improvement should collect real misrouted Active Directory and Software tickets before retraining.
        """
    )

    comparison = pd.DataFrame(
        [
            {"Experiment": "Run 2", "Change": "Targeted weak-class examples + larger LoRA", "Outcome": "Best overall model"},
            {"Experiment": "Run 3", "Change": "Added 55 boundary examples, 3 epochs", "Outcome": "Software improved; overall accuracy dropped"},
            {"Experiment": "Run 4", "Change": "Same as Run 3, 4 epochs", "Outcome": "No recovery; AD worsened"},
        ]
    )
    st.dataframe(comparison, width="stretch", hide_index=True)

with model_card:
    st.subheader("Model Card")
    card = pd.DataFrame(
        [
            {"Field": "Model name", "Value": "TicketRouter v2.0"},
            {"Field": "Base model", "Value": "Qwen/Qwen3-1.7B-Base"},
            {"Field": "Fine-tuning method", "Value": "LoRA adapter using LLaMA Factory"},
            {"Field": "Task", "Value": "7-class IT support ticket routing"},
            {"Field": "Selected run", "Value": "Run 2"},
            {"Field": "Validation accuracy", "Value": "77.8%"},
            {"Field": "Intended use", "Value": "Internal first-pass routing to resolver queues"},
            {"Field": "Safety layer", "Value": "Low-confidence predictions route to Support general for human review"},
            {"Field": "Known limitation", "Value": "Active Directory remains the most ambiguous class"},
            {"Field": "Privacy note", "Value": "IT tickets may contain account names, access requests, device IDs, and internal system names"},
        ]
    )
    st.dataframe(card, width="stretch", hide_index=True)

st.caption("Demo note: the UI uses a lightweight routing simulator for presentation. The model-selection evidence comes from the fine-tuned notebook experiments.")
