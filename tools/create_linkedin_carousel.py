from pathlib import Path
import textwrap

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project")
MEDIA = ROOT / "tmp" / "linkedin_carousel" / "media"
OUT_DIR = ROOT / "output" / "pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUT_DIR / "TicketRouter_LinkedIn_Carousel.pdf"
POST_PATH = OUT_DIR / "TicketRouter_LinkedIn_Post.txt"

W, H = 1080, 1080
NAVY = colors.HexColor("#0f172a")
BLUE = colors.HexColor("#2563eb")
LIGHT_BLUE = colors.HexColor("#dbeafe")
ORANGE = colors.HexColor("#f97316")
GREEN = colors.HexColor("#16a34a")
SLATE = colors.HexColor("#475569")
MUTED = colors.HexColor("#94a3b8")
BG = colors.HexColor("#f8fafc")
WHITE = colors.white


def wrap_text(text, font_name, font_size, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(c, text, x, y, max_width, font="Helvetica", size=26, color=NAVY, leading=None):
    c.setFont(font, size)
    c.setFillColor(color)
    leading = leading or size * 1.25
    lines = wrap_text(text, font, size, max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def pill(c, text, x, y, w, h, fill, stroke=None, text_color=NAVY, size=20):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(x + w / 2, y + h / 2 - size * 0.35, text)


def image_box(c, image_name, x, y, w, h, radius=18):
    path = MEDIA / image_name
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    c.setFillColor(WHITE)
    c.setStrokeColor(colors.HexColor("#e2e8f0"))
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.drawImage(ImageReader(img), x + (w - nw) / 2, y + (h - nh) / 2, nw, nh, preserveAspectRatio=True)


def footer(c, n):
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 18)
    c.drawString(72, 44, "TicketRouter - Qwen3-1.7B + LoRA")
    c.drawRightString(W - 72, 44, f"{n}/7")


def title(c, text, y=940, size=58):
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", size)
    for line in wrap_text(text, "Helvetica-Bold", size, W - 144):
        c.drawString(72, y, line)
        y -= size * 1.05
    return y


def new_page(c, n):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    footer(c, n)


def make_pdf():
    c = canvas.Canvas(str(PDF_PATH), pagesize=(W, H))

    # 1
    new_page(c, 1)
    pill(c, "Week 5 Builder Project", 72, 958, 280, 48, LIGHT_BLUE, text_color=BLUE)
    y = title(c, "I fine-tuned a 1.7B model to route IT support tickets", 850, 62)
    draw_wrapped(
        c,
        "TicketRouter turns messy helpdesk tickets into resolver-queue decisions using Qwen3-1.7B + LoRA.",
        72,
        y - 30,
        500,
        size=28,
        color=SLATE,
    )
    image_box(c, "image14.png", 560, 230, 450, 560)
    pill(c, "24.8% baseline", 72, 248, 210, 54, WHITE, stroke=colors.HexColor("#cbd5e1"), size=20)
    pill(c, "77.8% fine-tuned", 302, 248, 240, 54, colors.HexColor("#dcfce7"), text_color=GREEN, size=20)
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 40)
    c.drawString(72, 160, "+53.0 percentage points")
    c.showPage()

    # 2
    new_page(c, 2)
    title(c, "The problem was not generating answers. It was routing work.", 905, 50)
    draw_wrapped(
        c,
        "Internal IT tickets arrive through email, Slack, and portals. Before anyone can solve them, someone has to classify the request.",
        72,
        720,
        870,
        size=30,
        color=SLATE,
    )
    queues = ["O365", "Fileservice", "EOL", "Software", "Active Directory", "Computer-Services", "Support general"]
    x, y = 72, 520
    for i, q in enumerate(queues):
        pill(c, q, x, y, 292, 58, WHITE, stroke=colors.HexColor("#cbd5e1"), size=19)
        x += 318
        if x > 780:
            x = 72
            y -= 88
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(72, 180, "The model's job: first-pass triage only.")
    draw_wrapped(c, "No customer replies. No final approvals. Just route the ticket to the right queue.", 72, 132, 850, size=24, color=SLATE)
    c.showPage()

    # 3
    new_page(c, 3)
    title(c, "I chose LoRA because routing is behavior, not lookup.", 905, 50)
    draw_wrapped(c, "RAG was not the right fit. The system needed consistent classification patterns, not retrieved facts.", 72, 735, 860, size=30, color=SLATE)
    c.setStrokeColor(colors.HexColor("#bfdbfe"))
    c.setLineWidth(4)
    boxes = [("Qwen3-1.7B Base", 80), ("LoRA Adapter", 390), ("Ticket Router", 700)]
    for label, x in boxes:
        c.setFillColor(WHITE)
        c.roundRect(x, 455, 250, 150, 20, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(x + 125, 525, label)
    c.setStrokeColor(BLUE)
    c.line(330, 530, 390, 530)
    c.line(640, 530, 700, 530)
    pill(c, "Frozen base weights", 102, 350, 250, 52, LIGHT_BLUE, text_color=BLUE)
    pill(c, "Small trainable adapter", 398, 350, 300, 52, colors.HexColor("#ffedd5"), text_color=ORANGE)
    pill(c, "7-class decision", 745, 350, 220, 52, colors.HexColor("#dcfce7"), text_color=GREEN)
    draw_wrapped(c, "Result: lower training cost, smaller artifact, and enough capacity to learn IT routing language.", 72, 220, 880, size=28, color=SLATE)
    c.showPage()

    # 4
    new_page(c, 4)
    title(c, "Fine-tuning created routing capability the base model did not have.", 920, 46)
    image_box(c, "image7.png", 72, 292, 936, 490)
    pill(c, "Run 2 won", 72, 820, 170, 48, colors.HexColor("#dcfce7"), text_color=GREEN, size=21)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 46)
    c.drawString(72, 205, "24.8% -> 77.8% accuracy")
    draw_wrapped(c, "A +53.0 point lift over the base model, with macro F1 reaching 0.753.", 72, 148, 820, size=26, color=SLATE)
    c.showPage()

    # 5
    new_page(c, 5)
    title(c, "Four runs turned this into an engineering decision.", 920, 50)
    c.setFont("Helvetica-Bold", 25)
    c.setFillColor(NAVY)
    headers = ["Run", "Accuracy", "Macro F1", "Verdict"]
    xs = [80, 260, 450, 650]
    y = 730
    for h, x in zip(headers, xs):
        c.drawString(x, y, h)
    rows = [
        ("Run 1", "73.5%", "0.699", "Baseline established"),
        ("Run 2", "77.8%", "0.753", "Production candidate"),
        ("Run 3", "74.4%", "0.717", "Boundary data regressed"),
        ("Run 4", "74.4%", "0.718", "Epoch hypothesis rejected"),
    ]
    y -= 55
    for row in rows:
        fill = colors.HexColor("#dcfce7") if row[0] == "Run 2" else WHITE
        c.setFillColor(fill)
        c.roundRect(64, y - 18, 940, 48, 10, fill=1, stroke=0)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold" if row[0] == "Run 2" else "Helvetica", 24)
        for value, x in zip(row, xs):
            c.drawString(x, y, value)
        y -= 70
    draw_wrapped(
        c,
        "The best story was not just the score. It was proving that more examples and more epochs did not automatically improve the model.",
        72,
        300,
        900,
        size=30,
        color=SLATE,
    )
    c.showPage()

    # 6
    new_page(c, 6)
    title(c, "The failure analysis found the real bottleneck.", 930, 50)
    image_box(c, "image6.png", 70, 320, 510, 520)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(620, 700, "Weakest class:")
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 42)
    c.drawString(620, 642, "Active Directory")
    draw_wrapped(
        c,
        "Example miss: a contractor finance-group access request was predicted as O365 instead of Active Directory.",
        620,
        565,
        360,
        size=25,
        color=SLATE,
    )
    draw_wrapped(
        c,
        "The fix is better AD and Software examples, not simply longer training.",
        620,
        425,
        360,
        size=25,
        color=SLATE,
    )
    pill(c, "Data quality > data volume", 620, 320, 330, 56, colors.HexColor("#ffedd5"), text_color=ORANGE, size=22)
    c.showPage()

    # 7
    new_page(c, 7)
    title(c, "The final deliverable was a model decision, not just a notebook.", 920, 48)
    image_box(c, "image13.png", 72, 535, 430, 270)
    image_box(c, "image14.png", 578, 535, 430, 270)
    bullets = [
        "Merged model artifact hosted on Hugging Face",
        "Streamlit ops-console demo for the workflow",
        "Model card with limitations and rollback plan",
        "Controlled experiment narrative for why Run 2 won",
    ]
    y = 390
    for b in bullets:
        c.setFillColor(BLUE)
        c.circle(88, y + 8, 6, fill=1, stroke=0)
        draw_wrapped(c, b, 112, y, 820, size=28, color=NAVY)
        y -= 65
    c.setFillColor(ORANGE)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(72, 105, "Builder lesson: trust evidence, not vibes.")
    c.showPage()

    c.save()


def write_post():
    post = """I built TicketRouter, an IT support ticket routing system fine-tuned on Qwen3-1.7B with LoRA.

The goal was simple: take messy internal IT tickets and route them to the right resolver queue.

But the real learning was not just \"train a model.\" It was turning a notebook into an engineering decision: baseline, fine-tune, failure analysis, controlled experiments, production candidate, and deployment constraints.

The baseline model reached 24.8% accuracy.

The best fine-tuned run reached 77.8% accuracy, a +53 point improvement, with a macro F1 of 0.753.

I also tested additional runs to improve weak classes like Active Directory.

One concrete failure case: a contractor request for access to a finance distribution group was predicted as O365 instead of Active Directory. That kind of ambiguous access language is exactly where the model struggled.

The useful result: more epochs did not solve it. The bottleneck was data quality and label ambiguity, not training time.

That became the strongest part of the project.

I did not just submit a working notebook. I submitted a model decision story.

Stack: Qwen3-1.7B + LoRA via LLaMA Factory, trained in Colab, shipped with a Hugging Face model artifact, Streamlit ops-console demo, model card, and failure analysis.

Biggest takeaway: a good AI project is not just the model score. It is knowing why the model behaves the way it does, when to trust it, and when to route to human review.

Curious how others are handling ambiguous-label classes in production fine-tuning workflows.

#MachineLearning #FineTuning #LLM #AIEngineering #Streamlit #HuggingFace #MLOps #GenerativeAI
"""
    POST_PATH.write_text(post, encoding="utf-8")


if __name__ == "__main__":
    make_pdf()
    write_post()
    print(PDF_PATH)
    print(POST_PATH)
