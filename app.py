import os
import re

import streamlit as st


MODEL_ID = "Neog007/TicketRouter-1.7B"
BASE_MODEL_ID = "Qwen/Qwen3-1.7B-Base"
DEFAULT_REVIEW_THRESHOLD = 0.70
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

KEYWORD_RULES = [
    ("O365", ["outlook", "teams", "calendar", "office", "sharepoint", "onedrive", "mailbox"]),
    ("EOL", ["retire", "decommission", "old dell", "inventory", "monitoring", "end of life"]),
    ("Fileservice", ["shared drive", "shared folder", "network folder", "folder", "drive"]),
    ("Active Directory", ["active directory", "user account", "security group", "distribution group", "password reset"]),
    ("Software", ["install", "app", "application", "vpn client", "acrobat", "update failed", "error code"]),
    ("Computer-Services", ["workstation", "laptop", "desktop", "printer", "hardware", "device"]),
]


def get_config_value(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value

    try:
        value = st.secrets.get(name, default)
    except Exception:
        value = default

    return value or default


@st.cache_resource(show_spinner=False)
def load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

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

        from peft import PeftConfig, PeftModel

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
    import torch

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


def classify_demo(ticket: str) -> tuple[str, float]:
    text = ticket.lower()
    scores = {}
    for label, keywords in KEYWORD_RULES:
        scores[label] = sum(1 for keyword in keywords if keyword in text)

    label, score = max(scores.items(), key=lambda item: item[1])
    if score == 0:
        return "Support general", 0.51

    confidence = min(0.96, 0.58 + (score * 0.13))
    if label == "Active Directory" and any(term in text for term in ["shared", "folder", "drive", "teams"]):
        confidence = min(confidence, 0.66)
    return label, confidence


def route_via_cloud_run(ticket: str, review_threshold: float) -> dict:
    import requests

    api_url = get_config_value("TICKETROUTER_API_URL").rstrip("/")
    if not api_url:
        raise RuntimeError("TICKETROUTER_API_URL is not configured.")

    response = requests.post(
        f"{api_url}/route",
        json={"ticket": ticket, "review_threshold": review_threshold},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()


def show_model_error(exc: Exception) -> None:
    st.error("The Streamlit app is running, but the model could not be loaded.")
    st.code(str(exc), language="text")
    st.info(
        "For the live demo, the most reliable fix is to upload the fully merged model folder "
        "from Colab, not just the LoRA adapter folder. The merged folder should contain a "
        "valid config.json with a model_type field."
    )


def route_with_review_gate(label: str, ticket: str) -> tuple[str, str]:
    risky_terms = ["access", "permission", "group", "shared", "contractor", "new hire", "new employee"]
    is_ambiguous_access = any(term in ticket.lower() for term in risky_terms)
    if label in {"Active Directory", "Fileservice", "O365"} and is_ambiguous_access:
        return "Human review recommended", "Support general"
    return "Auto-route", label


st.set_page_config(page_title="TicketRouter-1.7B", layout="wide")

st.title("TicketRouter-1.7B")
st.caption("Fine-tuned Qwen3 model for IT support ticket routing | Neog007")

cloud_run_url = get_config_value("TICKETROUTER_API_URL")

with st.sidebar:
    st.header("Selected Model")
    st.success("Run 2 production candidate")
    inference_mode = st.radio(
        "Inference mode",
        ["Stable demo mode", "Cloud Run API", "Try Hugging Face model"],
        help="Cloud Run API uses the production-style backend when TICKETROUTER_API_URL is configured. Stable demo mode keeps the public Streamlit app responsive.",
    )
    review_threshold = st.slider(
        "Human review threshold",
        min_value=0.0,
        max_value=1.0,
        value=DEFAULT_REVIEW_THRESHOLD,
        step=0.05,
    )
    if cloud_run_url:
        st.caption("Cloud Run API configured.")
    else:
        st.caption("Cloud Run API not configured yet.")
    st.metric("Baseline accuracy", "24.8%")
    st.metric("Fine-tuned accuracy", "77.8%", "+53.0 pts")
    st.metric("Macro F1", "0.753")
    st.divider()
    st.write("Run 2 was selected after four controlled experiments because it had the best overall accuracy and macro F1.")
    st.caption("The full 1.7B model is hosted on Hugging Face; this UI defaults to a lightweight demo path for reliable public deployment.")

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
            if inference_mode == "Cloud Run API":
                with st.spinner("Routing through the Cloud Run model API..."):
                    try:
                        result = route_via_cloud_run(ticket, review_threshold)
                        label = result["predicted_label"]
                        confidence = result.get("confidence")
                        action = result["action"]
                        final_route = result["final_route"]
                    except Exception as exc:
                        show_model_error(exc)
                        st.stop()
            elif inference_mode == "Try Hugging Face model":
                with st.spinner("Loading Run 2 model and routing ticket..."):
                    try:
                        tokenizer, model = load_model()
                        label = classify(ticket, tokenizer, model)
                        confidence = None
                        action, final_route = route_with_review_gate(label, ticket)
                    except Exception as exc:
                        show_model_error(exc)
                        st.stop()
            else:
                with st.spinner("Routing with the deployment-safe demo router..."):
                    label, confidence = classify_demo(ticket)
                    action, final_route = route_with_review_gate(label, ticket)

            col1, col2, col3 = st.columns(3)
            col1.metric("Predicted Queue", label)
            col2.metric("Action", action)
            col3.metric("Final Route", final_route)
            if confidence is not None:
                source = "Cloud Run confidence" if inference_mode == "Cloud Run API" else "Demo confidence"
                st.caption(f"{source}: {confidence:.1%}. The notebook reports the real Run 2 validation score: 77.8% accuracy, macro F1 0.753.")

with tab_batch:
    st.subheader("Batch Routing")
    st.caption("Paste one ticket per line.")
    tickets = st.text_area("Tickets", value="\n".join(EXAMPLES), height=220)

    if st.button("Route Batch", type="primary"):
        rows = [line.strip() for line in tickets.splitlines() if line.strip()]
        if not rows:
            st.warning("Please enter at least one ticket.")
        else:
            with st.spinner("Routing batch..."):
                routed = []
                if inference_mode == "Cloud Run API":
                    try:
                        for row in rows:
                            result = route_via_cloud_run(row, review_threshold)
                            routed.append(
                                {
                                    "Ticket": row,
                                    "Predicted Queue": result["predicted_label"],
                                    "Confidence": f"{result.get('confidence', 0.0):.1%}",
                                    "Action": result["action"],
                                    "Final Route": result["final_route"],
                                }
                            )
                    except Exception as exc:
                        show_model_error(exc)
                        st.stop()
                elif inference_mode == "Try Hugging Face model":
                    try:
                        tokenizer, model = load_model()
                        for row in rows:
                            label = classify(row, tokenizer, model)
                            action, final_route = route_with_review_gate(label, row)
                            routed.append(
                                {
                                    "Ticket": row,
                                    "Predicted Queue": label,
                                    "Confidence": "model",
                                    "Action": action,
                                    "Final Route": final_route,
                                }
                            )
                    except Exception as exc:
                        show_model_error(exc)
                        st.stop()
                else:
                    for row in rows:
                        label, confidence = classify_demo(row)
                        action, final_route = route_with_review_gate(label, row)
                        routed.append(
                            {
                                "Ticket": row,
                                "Predicted Queue": label,
                                "Confidence": f"{confidence:.1%}",
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
    st.warning(
        "Deployment note: the full merged model is hosted on Hugging Face, but direct 1.7B CPU inference can exceed "
        "free Streamlit Cloud resources. The public app therefore defaults to a deployment-safe demo router and keeps "
        "the Hugging Face model path as an optional mode."
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
