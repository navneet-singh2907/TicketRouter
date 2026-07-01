import json
from pathlib import Path


SOURCE = Path("TicketRouter_Builder_Edition.ipynb")
TARGET = Path("TicketRouter_Run2_Targeted_Accuracy.ipynb")


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

# Make the title clearly identify the second experiment.
title = source_text(nb["cells"][0])
title = title.replace(
    "# Finetune Support Ticket Classifier Qwen3",
    "# TicketRouter Run 2 - Targeted Accuracy Experiment",
)
title += (
    "\n\n> Run 2 keeps the original validation split untouched, adds targeted "
    "training-only examples for weak classes, and uses a slightly larger LoRA "
    "adapter to test whether accuracy improves over Run 1."
)
set_source(nb["cells"][0], title)

# Patch dataset prep cell: split first, then append targeted train-only examples.
for cell in nb["cells"]:
    text = source_text(cell)
    if "sharegpt_records = [" in text and "df_train, df_val = train_test_split" in text:
        text = text.replace(
            'print(f"\\nTrain: {len(df_train):,} rows | Val (held-out): {len(df_val):,} rows")\n'
            'print("\\nTrain label distribution:")\n'
            'print(df_train["label"].value_counts())\n\n'
            '# ── 4. Convert train split → ShareGPT JSON ────────────────────────────────────',
            'print(f"\\nTrain before augmentation: {len(df_train):,} rows | Val (held-out): {len(df_val):,} rows")\n'
            'print("\\nTrain label distribution before augmentation:")\n'
            'print(df_train["label"].value_counts())\n\n'
            '# ── 4. Run 2 targeted training-only augmentation ─────────────────────────────\n'
            '# The validation split stays untouched so Run 1 and Run 2 remain comparable.\n'
            'targeted_examples = [\n'
            '    # Active Directory: account lifecycle, access groups, lockouts, MFA\n'
            '    {"text": "Please create an Active Directory account for the new analyst and add them to the Finance security group.", "label": "Active Directory"},\n'
            '    {"text": "New hire needs AD group membership for payroll and the VPN users security group.", "label": "Active Directory"},\n'
            '    {"text": "Please disable the Active Directory account for the contractor whose assignment ended Friday.", "label": "Active Directory"},\n'
            '    {"text": "User is locked out of their domain account after too many failed login attempts.", "label": "Active Directory"},\n'
            '    {"text": "Please reset the employee domain password and force a password change at next login.", "label": "Active Directory"},\n'
            '    {"text": "Add this user to the Active Directory security group for the finance shared applications.", "label": "Active Directory"},\n'
            '    {"text": "Remove the departed employee from all AD groups and deactivate the domain account.", "label": "Active Directory"},\n'
            '    {"text": "The new contractor needs access to the VPN users group and standard domain login.", "label": "Active Directory"},\n'
            '    {"text": "Please unlock my Windows domain account; I cannot authenticate to any company systems.", "label": "Active Directory"},\n'
            '    {"text": "Provision an AD account for the intern and assign the default onboarding security groups.", "label": "Active Directory"},\n'
            '    {"text": "User cannot complete MFA enrollment tied to their directory account.", "label": "Active Directory"},\n'
            '    {"text": "Please remove temporary admin group membership from this employee account.", "label": "Active Directory"},\n'
            '    {"text": "Manager approved access group changes for the employee in Active Directory.", "label": "Active Directory"},\n'
            '    {"text": "Employee changed departments and needs their AD group memberships updated.", "label": "Active Directory"},\n'
            '    {"text": "Please create a service account in Active Directory for the reporting job.", "label": "Active Directory"},\n'
            '    {"text": "Disable the service account that is no longer used by the legacy integration.", "label": "Active Directory"},\n'
            '    {"text": "User account shows expired in directory and needs reactivation after leave.", "label": "Active Directory"},\n'
            '    {"text": "Please add the new employee to the corporate distribution group and security role.", "label": "Active Directory"},\n'
            '    {"text": "Contractor cannot log in because their domain account was not provisioned.", "label": "Active Directory"},\n'
            '    {"text": "Offboarding request: disable AD login and remove security group memberships.", "label": "Active Directory"},\n'
            '    # Software: non-O365 apps, installs, licensing, crashes, updates\n'
            '    {"text": "Adobe Acrobat installation fails with error code 1603 on my workstation.", "label": "Software"},\n'
            '    {"text": "The VPN client update failed and now the application will not launch.", "label": "Software"},\n'
            '    {"text": "I need a license assigned for Tableau Desktop.", "label": "Software"},\n'
            '    {"text": "Zoom crashes immediately after the latest update.", "label": "Software"},\n'
            '    {"text": "Please install Python and VS Code on my laptop for development work.", "label": "Software"},\n'
            '    {"text": "The accounting application opens but freezes when I export a report.", "label": "Software"},\n'
            '    {"text": "Antivirus client is stuck updating and shows a software error.", "label": "Software"},\n'
            '    {"text": "I need the approved browser plugin installed for the CRM tool.", "label": "Software"},\n'
            '    {"text": "The CAD software license server says no seats are available.", "label": "Software"},\n'
            '    {"text": "Slack desktop app will not start after reinstalling.", "label": "Software"},\n'
            '    # O365: Outlook, Teams, SharePoint, mailbox, calendar, Office apps\n'
            '    {"text": "Outlook calendar invites are not syncing into Teams meetings.", "label": "O365"},\n'
            '    {"text": "My Teams status is stuck as offline even though Outlook is open.", "label": "O365"},\n'
            '    {"text": "SharePoint document library is not loading for my project team.", "label": "O365"},\n'
            '    {"text": "I cannot send email from the shared mailbox in Outlook.", "label": "O365"},\n'
            '    {"text": "OneDrive is not syncing the files in my company folder.", "label": "O365"},\n'
            '    {"text": "Excel online cannot open a workbook stored in SharePoint.", "label": "O365"},\n'
            '    {"text": "Teams meeting recordings are not appearing in the channel.", "label": "O365"},\n'
            '    {"text": "My mailbox is full and Outlook will not receive new messages.", "label": "O365"},\n'
            '    {"text": "PowerPoint in Microsoft 365 keeps prompting me to sign in.", "label": "O365"},\n'
            '    {"text": "The shared calendar permissions in Outlook are not working.", "label": "O365"},\n'
            ']\n\n'
            'df_aug = pd.DataFrame(targeted_examples)\n'
            'df_train = pd.concat([df_train, df_aug], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)\n'
            'print(f"\\nAdded {len(df_aug)} targeted training-only examples for Run 2.")\n'
            'print(f"Train after augmentation: {len(df_train):,} rows | Val still held out: {len(df_val):,} rows")\n'
            'print("\\nTrain label distribution after augmentation:")\n'
            'print(df_train["label"].value_counts())\n\n'
            '# ── 5. Convert train split → ShareGPT JSON ────────────────────────────────────',
        )
        text = text.replace("# ── 5. Register dataset", "# ── 6. Register dataset")
        text = text.replace("# ── 6. Save val split", "# ── 7. Save val split")
        set_source(cell, text)
        break

# Insert a clear Run 2 settings note before the LLaMA Board cell.
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "code" and "llamafactory-cli webui" in source_text(cell):
        nb["cells"].insert(
            i,
            md(
                """
### Run 2 Training Settings

Use the same model/dataset setup as Run 1, but increase adapter capacity slightly:

| Setting | Run 2 value |
|---|---|
| Model | `Qwen/Qwen3-1.7B-Base` |
| Dataset | `support_tickets` |
| Stage | `sft` |
| Finetuning type | `lora` |
| Compute type | `fp16` |
| Epochs | `4` |
| Learning rate | `5e-5` |
| Batch size | `2` |
| Gradient accumulation | `8` |
| LoRA rank | `16` |
| LoRA alpha | `32` |
| LoRA dropout | `0.05` |
| LoRA target | `all` |
| Val size | `0` |

Keep the validation split from the notebook untouched so Run 2 can be compared fairly against Run 1.
"""
            ),
        )
        break

# Patch classification reports and comparison chart to use explicit labels.
for cell in nb["cells"]:
    text = source_text(cell)
    if "print(classification_report(y_true, y_pred, target_names=LABEL_TOKENS" in text:
        text = text.replace(
            "print(classification_report(y_true, y_pred, target_names=LABEL_TOKENS, digits=3))",
            "print(classification_report(y_true, y_pred, labels=LABEL_TOKENS, target_names=LABEL_TOKENS, digits=3, zero_division=0))",
        )
        set_source(cell, text)
    if "def per_class_f1(y_t, y_p, labels):" in text:
        text = text.replace(
            "report = classification_report(y_t, y_p, target_names=labels, output_dict=True, zero_division=0)",
            "report = classification_report(y_t, y_p, labels=labels, target_names=labels, output_dict=True, zero_division=0)",
        )
        set_source(cell, text)

# Patch confusion matrix recall diagnostics.
for cell in nb["cells"]:
    text = source_text(cell)
    if 'print(f"\\nActive Directory recall' in text:
        old = '''ad_recall   = cm_norm[LABEL_TOKENS.index("Active Directory"),   LABEL_TOKENS.index("Active Directory")]
file_recall = cm_norm[LABEL_TOKENS.index("Fileservice"),        LABEL_TOKENS.index("Fileservice")]
print(f"\\nActive Directory recall : {ad_recall:.1%}")
print(f"Fileservice recall      : {file_recall:.1%}")
if ad_recall < 0.85:
    print("Warning: Active Directory recall below 0.85 — consider training longer.")'''
        new = '''print("\\nPer-class recall:")
for label in LABEL_TOKENS:
    idx = LABEL_TOKENS.index(label)
    recall = cm_norm[idx, idx]
    print(f"{label:<20}: {recall:.1%}")

weakest_idx = cm_norm.diagonal().argmin()
weakest_label = LABEL_TOKENS[weakest_idx]
weakest_recall = cm_norm[weakest_idx, weakest_idx]

print(f"\\nWeakest recall: {weakest_label} ({weakest_recall:.1%})")
if weakest_recall < 0.85:
    print(f"Warning: {weakest_label} recall below 0.85 - investigate confusion matrix and add more examples.")'''
        text = text.replace(old, new)
        set_source(cell, text)
        break

# Add a comparison table template after the final chart.
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "code" and 'print(f"\\nBase accuracy' in source_text(cell):
        nb["cells"].insert(
            i + 1,
            md(
                """
---
## Run 2 Decision Check

Compare Run 2 against the preserved Run 1 result:

| Metric | Run 1 | Run 2 |
|---|---:|---:|
| Fine-tuned accuracy | 73.5% | Fill after evaluation |
| Active Directory F1 | 0.308 | Fill after evaluation |
| Software F1 | 0.600 | Fill after evaluation |
| O365 F1 | 0.684 | Fill after evaluation |

Keep Run 2 only if overall accuracy improves or the weak classes improve without damaging the stronger classes too much.
"""
            ),
        )
        break

TARGET.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Created {TARGET} from {SOURCE} with {len(nb['cells'])} cells.")
