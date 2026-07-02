import json
from pathlib import Path


SOURCE = Path("TicketRouter_Run3_Failure_Driven.ipynb")
TARGET = Path("TicketRouter_Run4_Failure_Driven_4Epochs.ipynb")


def source_text(cell: dict) -> str:
    return "".join(cell.get("source", []))


def set_source(cell: dict, text: str) -> None:
    cell["source"] = [line + "\n" for line in text.strip().split("\n")]


nb = json.loads(SOURCE.read_text(encoding="utf-8"))

for cell in nb["cells"]:
    text = source_text(cell)
    if "# TicketRouter Run 3 - Failure-Driven Accuracy Experiment" in text:
        text = text.replace(
            "# TicketRouter Run 3 - Failure-Driven Accuracy Experiment",
            "# TicketRouter Run 4 - Failure-Driven 4-Epoch Experiment",
        )
        text = text.replace(
            "> Run 3 keeps the validation split untouched and adds failure-driven boundary examples based on Run 2's confusion matrix: Active Directory vs Support general/O365, plus Software vs O365/general app issues.",
            "> Run 4 keeps the Run 3 failure-driven boundary dataset, but increases training from 3 epochs to 4 epochs to test whether extra training improves validation accuracy and weak-class recall.",
        )
        set_source(cell, text)
        break

for cell in nb["cells"]:
    text = source_text(cell)
    if "### Run 3 Training Settings" in text:
        text = text.replace("### Run 3 Training Settings", "### Run 4 Training Settings")
        text = text.replace("Run 3 is a failure-driven retrain.", "Run 4 is a controlled follow-up to Run 3.")
        text = text.replace("| Setting | Run 3 value |", "| Setting | Run 4 value |")
        text = text.replace("| Epochs | `3` |", "| Epochs | `4` |")
        text = text.replace(
            "| Output dir | use a fresh path like `saves/Qwen3-1.7B-Base/lora/train_v3_YYYYMMDD_HHMMSS` |",
            "| Output dir | use a fresh path like `saves/Qwen3-1.7B-Base/lora/train_v4_YYYYMMDD_HHMMSS` |",
        )
        text = text.replace(
            "Why these changes: Run 2 already converged very strongly, so Run 3 adds better boundary data and uses a slightly lower learning rate/epoch count to improve generalization instead of simply memorizing.",
            "Why this run: Run 4 changes only the epoch count from Run 3. If validation improves, extra training helped. If validation drops, Run 3/Run 2 were better generalization choices.",
        )
        set_source(cell, text)
        break

for cell in nb["cells"]:
    text = source_text(cell)
    if "## Run 3 Decision Check" in text:
        text = text.replace("## Run 3 Decision Check", "## Run 4 Decision Check")
        text = text.replace("Compare Run 3 against Run 2", "Compare Run 4 against Run 2 and Run 3")
        text = text.replace("| Metric | Run 2 | Run 3 |", "| Metric | Run 2 | Run 3 | Run 4 |")
        text = text.replace("|---|---:|---:|", "|---|---:|---:|---:|")
        text = text.replace("| Fine-tuned accuracy | 77.8% | Fill after evaluation |", "| Fine-tuned accuracy | 77.8% | 74.4% | Fill after evaluation |")
        text = text.replace("| Macro F1 | 0.753 | Fill after evaluation |", "| Macro F1 | 0.753 | 0.717 | Fill after evaluation |")
        text = text.replace("| Active Directory F1 | 0.471 | Fill after evaluation |", "| Active Directory F1 | 0.471 | 0.308 | Fill after evaluation |")
        text = text.replace("| Active Directory recall | 44.4% | Fill after evaluation |", "| Active Directory recall | 44.4% | 22.2% | Fill after evaluation |")
        text = text.replace("| Software F1 | 0.522 | Fill after evaluation |", "| Software F1 | 0.522 | 0.609 | Fill after evaluation |")
        text = text.replace("| O365 F1 | 0.842 | Fill after evaluation |", "| O365 F1 | 0.842 | 0.750 | Fill after evaluation |")
        text = text.replace(
            "Keep Run 3 only if it improves Active Directory and Software without dropping overall accuracy too much. If accuracy falls but Active Directory improves clearly, describe it as a tradeoff experiment and submit Run 2 as the production candidate.",
            "Keep Run 4 only if it recovers overall accuracy and improves Active Directory or Software. If it mainly memorizes and validation drops, keep Run 2 as the production candidate.",
        )
        set_source(cell, text)
        break

for cell in nb["cells"]:
    text = source_text(cell)
    if "TicketRouter v3.0 candidate" in text:
        text = text.replace("TicketRouter v3.0 candidate", "TicketRouter v4.0 experiment")
        set_source(cell, text)
        break

TARGET.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Created {TARGET} from {SOURCE} with {len(nb['cells'])} cells.")
