import json
from pathlib import Path


SOURCE = Path("TicketRouter_Run2_Targeted_Accuracy.ipynb")
TARGET = Path("TicketRouter_Run3_Failure_Driven.ipynb")


def source_text(cell: dict) -> str:
    return "".join(cell.get("source", []))


def set_source(cell: dict, text: str) -> None:
    cell["source"] = [line + "\n" for line in text.strip().split("\n")]


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.strip().split("\n")],
    }


nb = json.loads(SOURCE.read_text(encoding="utf-8"))

# Make the title clearly identify the third experiment.
for cell in nb["cells"]:
    if cell.get("cell_type") == "markdown" and "TicketRouter Run 2" in source_text(cell):
        text = source_text(cell)
        text = text.replace(
            "# TicketRouter Run 2 - Targeted Accuracy Experiment",
            "# TicketRouter Run 3 - Failure-Driven Accuracy Experiment",
        )
        text = text.replace(
            "> Run 2 keeps the original validation split untouched, adds targeted training-only examples for weak classes, and uses a slightly larger LoRA adapter to test whether accuracy improves over Run 1.",
            "> Run 3 keeps the validation split untouched and adds failure-driven boundary examples based on Run 2's confusion matrix: Active Directory vs Support general/O365, plus Software vs O365/general app issues.",
        )
        set_source(cell, text)
        break

# Add Run 3 boundary examples after the Run 2 targeted examples are loaded.
for cell in nb["cells"]:
    text = source_text(cell)
    marker = 'df_aug = pd.DataFrame(targeted_examples)\n'
    if marker in text and "targeted_examples = [" in text:
        addition = '''df_aug = pd.DataFrame(targeted_examples)

# Run 3: failure-driven boundary examples from Run 2 confusion matrix.
# These are training-only examples. The validation set remains untouched.
run3_boundary_examples = [
    # Active Directory: make identity/access intent explicit even when wording is vague.
    {"text": "New contractor needs an Active Directory account and membership in the finance security group.", "label": "Active Directory"},
    {"text": "Please provision a domain login for the new finance contractor and add the correct AD groups.", "label": "Active Directory"},
    {"text": "The employee moved teams and needs their Active Directory security groups updated.", "label": "Active Directory"},
    {"text": "Please add the analyst to the Finance distribution group and the reporting security group.", "label": "Active Directory"},
    {"text": "User cannot access internal apps because their AD group membership is missing.", "label": "Active Directory"},
    {"text": "Create a domain account for the new employee and assign standard onboarding groups.", "label": "Active Directory"},
    {"text": "Offboarding request: disable the user's domain account and remove all directory groups.", "label": "Active Directory"},
    {"text": "Please unlock the user's Active Directory account after failed login attempts.", "label": "Active Directory"},
    {"text": "Reset the Windows domain password and require change at next sign-in.", "label": "Active Directory"},
    {"text": "Add the service account to the approved AD security group for the integration.", "label": "Active Directory"},
    {"text": "Remove temporary admin group membership from this user's directory account.", "label": "Active Directory"},
    {"text": "Contractor extension approved; reactivate their domain account and VPN users group.", "label": "Active Directory"},
    {"text": "Manager approved security group access for the new hire in Active Directory.", "label": "Active Directory"},
    {"text": "User's directory account is expired and needs to be re-enabled after leave.", "label": "Active Directory"},
    {"text": "Please add the employee to the payroll distribution list and AD security role.", "label": "Active Directory"},
    {"text": "New analyst needs domain login plus finance app access group membership.", "label": "Active Directory"},
    {"text": "Please disable login for the terminated employee and remove directory access.", "label": "Active Directory"},
    {"text": "The shared app denies access because the user's AD role is not assigned.", "label": "Active Directory"},
    {"text": "Create an Active Directory service account for the scheduled reporting job.", "label": "Active Directory"},
    {"text": "Please remove the old service account from all AD groups before deletion.", "label": "Active Directory"},
    {"text": "User cannot authenticate to VPN because their domain account is locked.", "label": "Active Directory"},
    {"text": "Please update the contractor's directory group membership for the finance project.", "label": "Active Directory"},
    {"text": "Give the new employee the standard domain account and department security groups.", "label": "Active Directory"},
    {"text": "MFA enrollment is blocked for this user's directory account.", "label": "Active Directory"},
    {"text": "Need to add three users to the HR security group in Active Directory.", "label": "Active Directory"},

    # Software: non-Microsoft-365 app installs, crashes, updates, and licenses.
    {"text": "Adobe Acrobat installer fails with error 1603 after the latest Windows update.", "label": "Software"},
    {"text": "The VPN desktop client crashes every time I launch it.", "label": "Software"},
    {"text": "Please install Notepad++ and 7-Zip on my workstation.", "label": "Software"},
    {"text": "Tableau Desktop license key is not activating on my laptop.", "label": "Software"},
    {"text": "The Zoom desktop application freezes when joining meetings.", "label": "Software"},
    {"text": "The accounting desktop app throws a runtime error when exporting invoices.", "label": "Software"},
    {"text": "Chrome extension required for the CRM tool is missing from my browser.", "label": "Software"},
    {"text": "The antivirus agent update is stuck and reports a software installation error.", "label": "Software"},
    {"text": "Please deploy the approved PDF editor to this user's laptop.", "label": "Software"},
    {"text": "The CAD application opens but cannot check out a license.", "label": "Software"},
    {"text": "Slack desktop app will not start after reinstall.", "label": "Software"},
    {"text": "Python and VS Code need to be installed for the engineering team.", "label": "Software"},
    {"text": "The VPN client says the installed version is unsupported.", "label": "Software"},
    {"text": "Printer management software fails to launch on the workstation.", "label": "Software"},
    {"text": "The backup client is throwing an application error after the patch.", "label": "Software"},

    # Boundary negatives: these teach when access wording is Fileservice/O365/Support general, not AD.
    {"text": "I can log in, but the marketing folder on the shared drive says access denied.", "label": "Fileservice"},
    {"text": "The shared network folder opens for others but not for me.", "label": "Fileservice"},
    {"text": "Please restore a deleted folder from the department file share.", "label": "Fileservice"},
    {"text": "The team drive path is missing from File Explorer.", "label": "Fileservice"},
    {"text": "Outlook says I do not have permission to send from the shared mailbox.", "label": "O365"},
    {"text": "Teams will not let me join a meeting from my Outlook calendar invite.", "label": "O365"},
    {"text": "SharePoint says the document library is unavailable for my project.", "label": "O365"},
    {"text": "OneDrive sync is paused and my Microsoft 365 files are not updating.", "label": "O365"},
    {"text": "I am not sure which team handles this request; please triage it.", "label": "Support general"},
    {"text": "I need help deciding where this IT issue should go.", "label": "Support general"},
]

df_run3 = pd.DataFrame(run3_boundary_examples)
df_aug = pd.concat([df_aug, df_run3], ignore_index=True)
'''
        text = text.replace(marker, addition)
        text = text.replace(
            'print(f"\\nAdded {len(df_aug)} targeted training-only examples for Run 2.")',
            'print(f"\\nAdded {len(df_aug)} targeted + boundary training-only examples for Run 3.")',
        )
        text = text.replace(
            "Train after augmentation:",
            "Train after Run 3 augmentation:",
        )
        set_source(cell, text)
        break

# Replace Run 2 training note with Run 3 settings.
for cell in nb["cells"]:
    if cell.get("cell_type") == "markdown" and "### Run 2 Training Settings" in source_text(cell):
        set_source(
            cell,
            """
### Run 3 Training Settings

Run 3 is a failure-driven retrain. Use the same base model, but train on the expanded boundary dataset and avoid overtraining:

| Setting | Run 3 value |
|---|---|
| Model | `Qwen/Qwen3-1.7B-Base` |
| Dataset | `support_tickets` |
| Stage | `sft` |
| Finetuning type | `lora` |
| Compute type | `fp16` |
| Epochs | `3` |
| Learning rate | `3e-5` |
| Batch size | `2` |
| Gradient accumulation | `8` |
| LoRA rank | `16` |
| LoRA alpha | `32` |
| LoRA dropout | `0.05` |
| LoRA target | `all` |
| Val size | `0` |
| Output dir | use a fresh path like `saves/Qwen3-1.7B-Base/lora/train_v3_YYYYMMDD_HHMMSS` |

Why these changes: Run 2 already converged very strongly, so Run 3 adds better boundary data and uses a slightly lower learning rate/epoch count to improve generalization instead of simply memorizing.
""",
        )
        break

# Update model card wording for Run 3 if present.
for cell in nb["cells"]:
    text = source_text(cell)
    if "TicketRouter v1.0" in text and "Builder Edition: Model Card" in text:
        text = text.replace("TicketRouter v1.0", "TicketRouter v3.0 candidate")
        text = text.replace(
            "Ambiguous access tickets may confuse Fileservice and Active Directory; Office app issues may confuse O365 and Software; rare labels need more data",
            "Active Directory and Software are the primary monitored classes; ambiguous access tickets require confidence-gated review",
        )
        set_source(cell, text)
        break

# Add a Run 3 decision check near the final comparison chart.
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "markdown" and "## Run 2 Decision Check" in source_text(cell):
        set_source(
            cell,
            """
---
## Run 3 Decision Check

Compare Run 3 against Run 2 before deciding which model to submit:

| Metric | Run 2 | Run 3 |
|---|---:|---:|
| Fine-tuned accuracy | 77.8% | Fill after evaluation |
| Macro F1 | 0.753 | Fill after evaluation |
| Active Directory F1 | 0.471 | Fill after evaluation |
| Active Directory recall | 44.4% | Fill after evaluation |
| Software F1 | 0.522 | Fill after evaluation |
| O365 F1 | 0.842 | Fill after evaluation |

Keep Run 3 only if it improves Active Directory and Software without dropping overall accuracy too much. If accuracy falls but Active Directory improves clearly, describe it as a tradeoff experiment and submit Run 2 as the production candidate.
""",
        )
        break

TARGET.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Created {TARGET} from {SOURCE} with {len(nb['cells'])} cells.")
