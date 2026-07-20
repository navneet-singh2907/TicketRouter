import os
import re
from functools import lru_cache
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ID = os.getenv("MODEL_ID", "Neog007/TicketRouter-1.7B")
HF_TOKEN = os.getenv("HF_TOKEN")
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.70"))

LABELS = [
    "Active Directory",
    "Computer-Services",
    "EOL",
    "Fileservice",
    "O365",
    "Software",
    "Support general",
]

RISKY_ACCESS_TERMS = [
    "access",
    "permission",
    "group",
    "shared",
    "contractor",
    "new hire",
    "new employee",
]


class RouteRequest(BaseModel):
    ticket: str = Field(..., min_length=1, max_length=4000)
    review_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class RouteResponse(BaseModel):
    predicted_label: str
    final_route: str
    confidence: float
    action: str
    model_id: str


app = FastAPI(
    title="TicketRouter API",
    description="Cloud Run inference API for the TicketRouter Qwen3 + LoRA model.",
    version="1.0.0",
)


def normalize_label(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\-\s]", "", text).strip()
    for label in LABELS:
        if label.lower() in cleaned.lower():
            return label

    first_line = cleaned.splitlines()[0].strip() if cleaned else ""
    return first_line if first_line in LABELS else "Support general"


def build_prompt(ticket: str) -> str:
    return (
        "<|im_start|>system\n"
        "Route this IT support ticket to exactly one queue. "
        f"Allowed queues: {', '.join(LABELS)}. "
        "Return only the queue name."
        "<|im_end|>\n"
        f"<|im_start|>user\n{ticket}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )


def confidence_from_scores(outputs) -> float:
    if not outputs.scores:
        return 0.0

    token_confidences = []
    for score_tensor in outputs.scores:
        probs = torch.softmax(score_tensor[0].float(), dim=-1)
        token_confidences.append(float(torch.max(probs).item()))

    if not token_confidences:
        return 0.0

    return sum(token_confidences) / len(token_confidences)


def apply_review_gate(label: str, confidence: float, ticket: str, threshold: float) -> tuple[str, str]:
    ambiguous_access = any(term in ticket.lower() for term in RISKY_ACCESS_TERMS)
    needs_review = confidence < threshold or (
        label in {"Active Directory", "Fileservice", "O365"} and ambiguous_access and confidence < 0.90
    )

    if needs_review:
        return "Human review required", "Support general"

    return "Auto-route", label


@lru_cache(maxsize=1)
def load_model():
    auth_kwargs = {"token": HF_TOKEN} if HF_TOKEN else {}
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True, **auth_kwargs)

    if torch.cuda.is_available():
        dtype = torch.bfloat16
        device_map = "auto"
    else:
        dtype = torch.float32
        device_map = None

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        device_map=device_map,
        **auth_kwargs,
    )
    model.eval()
    return tokenizer, model


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_id": MODEL_ID,
        "model_loaded": load_model.cache_info().currsize > 0,
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/route", response_model=RouteResponse)
def route_ticket(request: RouteRequest):
    ticket = request.ticket.strip()
    if not ticket:
        raise HTTPException(status_code=400, detail="ticket cannot be empty")

    try:
        tokenizer, model = load_model()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"model load failed: {exc}") from exc

    prompt = build_prompt(ticket)
    inputs = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        inputs = {key: value.to(model.device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=12,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            return_dict_in_generate=True,
            output_scores=True,
        )

    generated = outputs.sequences[0][inputs["input_ids"].shape[1] :]
    decoded = tokenizer.decode(generated, skip_special_tokens=True)
    label = normalize_label(decoded)
    confidence = confidence_from_scores(outputs)
    threshold = request.review_threshold if request.review_threshold is not None else REVIEW_THRESHOLD
    action, final_route = apply_review_gate(label, confidence, ticket, threshold)

    return RouteResponse(
        predicted_label=label,
        final_route=final_route,
        confidence=confidence,
        action=action,
        model_id=MODEL_ID,
    )
