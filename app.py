import os
import re

import streamlit as st
import torch
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ID = "Neog007/TicketRouter-1.7B"
BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
LABELS = [
    "Active Directory",
    "Computer-Services",
    "EOL",
    "Fileservice",
    "O365",
    "Software",
    "Support general",
]

EXAMPLES = [
    "My Outlook calendar invites are not showing up in Teams meetings.",
    "Please create an Active Directory user account and assign standard finance security groups.",
    "I can open the shared drive but not the marketing folder inside it.",
    "Please remove the old Dell workstation in room 204 from inventory and monitoring.",
    "The VPN client update failed and now the app will not launch.",
]


@st.cache_resource(show_spinner=False)
def load_model():
    token = st.secrets.get("HF_TOKEN", os.getenv("HF_TOKEN")) if hasattr(st, "secrets") else os.getenv("HF_TOKEN")
    auth_kwargs = {"token": token} if token else {}
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, **auth_kwargs)
    try:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            **auth_kwargs,
        )
    except ValueError as exc:
        if "model_type" not in str(exc):
            raise

        adapter_config = PeftConfig.from_pretrained(MODEL_ID, **auth_kwargs)
        base_model_id = adapter_config.base_model_name_or_path or BASE_MODEL_ID
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            **auth_kwargs,
        )
        model = PeftModel.from_pretrained(base_model, MODEL_ID, **auth_kwargs)
    model.eval()
    return tokenizer, model


def normalize_label(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\-\s]", "", text).strip()
    for label in LABELS:
        if label.lower() in cleaned.lower():
            return label
    first_line = cleaned.splitlines()[0].strip() if cleaned else "Support general"
    return first_line if first_line in LABELS else "Support general"


def classify(ticket: str, tokenizer, model) -> str:
    prompt = (
        "<|im_start|>system\n"
        "Route this IT support ticket to exactly one queue. "
        f"Allowed queues: {', '.join(LABELS)}. "
        "Return only the queue name."
        "<|im_end|>\n"
        f"<|im_start|>user\n{ticket}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=12,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    result = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)
    return normalize_label(result)


def route_with_review_gate(label: str, ticket: str) -> tuple[str, str]:
    risky_terms = ["access", "permission", "group", "shared", "contractor", "new hire", "new employee"]
    is_ambiguous_access = any(term in ticket.lower() for term in risky_terms)
    if label in {"Active Directory", "Fileservice", "O365"} and is_ambiguous_access:
        return "Human review recommended", "Support general"
    return "Auto-route", label


st.set_page_config(page_title="TicketRouter-1.7B", layout="wide")

st.title("TicketRouter-1.7B")
st.caption("Fine-tuned Qwen3 model for IT support ticket routing | Neog007")

with st.sidebar:
    st.header("Selected Model")
    st.success("Run 2 production candidate")
    st.metric("Baseline accuracy", "24.8%")
    st.metric("Fine-tuned accuracy", "77.8%", "+53.0 pts")
    st.metric("Macro F1", "0.753")
    st.divider()
    st.write("Run 2 was selected after four controlled experiments because it had the best overall accuracy and macro F1.")

tab_route, tab_batch, tab_results, tab_card = st.tabs(
    ["Route Ticket", "Batch Routing", "Experiment Results", "Model Card"]
)

with tab_route:
    st.subheader("Single Ticket Routing")
    selected = st.selectbox("Load an example", ["Custom"] + EXAMPLES)
    initial_ticket = "" if selected == "Custom" else selected
    ticket = st.text_area("Paste your IT support ticket here:", value=initial_ticket, height=150)

    if st.button("Route Ticket", type="primary"):
        if not ticket.strip():
            st.warning("Please enter a ticket first.")
        else:
            with st.spinner("Loading Run 2 model and routing ticket..."):
                tokenizer, model = load_model()
                label = classify(ticket, tokenizer, model)
                action, final_route = route_with_review_gate(label, ticket)

            col1, col2, col3 = st.columns(3)
            col1.metric("Predicted Queue", label)
            col2.metric("Action", action)
            col3.metric("Final Route", final_route)

with tab_batch:
    st.subheader("Batch Routing")
    st.caption("Paste one ticket per line.")
    tickets = st.text_area("Tickets", value="\n".join(EXAMPLES), height=220)

    if st.button("Route Batch", type="primary"):
        rows = [line.strip() for line in tickets.splitlines() if line.strip()]
        if not rows:
            st.warning("Please enter at least one ticket.")
        else:
            with st.spinner("Routing batch with Run 2 model..."):
                tokenizer, model = load_model()
                routed = []
                for row in rows:
                    label = classify(row, tokenizer, model)
                    action, final_route = route_with_review_gate(label, row)
                    routed.append(
                        {
                            "Ticket": row,
                            "Predicted Queue": label,
                            "Action": action,
                            "Final Route": final_route,
                        }
                    )
            st.dataframe(routed, width="stretch", hide_index=True)

with tab_results:
    st.subheader("Controlled Experiment Results")
    st.markdown(
        """
        | Metric | Run 1 | Run 2 | Run 3 | Run 4 |
        |---|---:|---:|---:|---:|
        | Accuracy | 73.5% | **77.8%** | 74.4% | 74.4% |
        | Active Directory F1 | 0.308 | **0.471** | 0.308 | 0.267 |
        | Software F1 | 0.600 | 0.522 | **0.609** | 0.583 |
        | Macro F1 | 0.699 | **0.753** | 0.717 | 0.718 |
        """
    )
    st.info(
        "Run 2 was selected as the production candidate. Run 3 and Run 4 showed that the remaining "
        "Active Directory weakness is a data-quality issue, not simply an epoch-count issue."
    )

with tab_card:
    st.subheader("Model Card")
    st.markdown(
        """
        | Field | Value |
        |---|---|
        | Model name | TicketRouter-1.7B |
        | Base model | Qwen/Qwen3-1.7B-Base |
        | Fine-tuning method | LoRA adapter using LLaMA Factory |
        | Selected run | Run 2 |
        | Task | 7-class IT support ticket routing |
        | Intended use | Internal first-pass routing to resolver queues |
        | Not intended for | Customer replies, final approvals, or irreversible account actions |
        | Known limitation | Active Directory remains the most ambiguous class |
        | Privacy note | IT tickets can contain account names, access requests, device IDs, and internal systems |
        """
    )
