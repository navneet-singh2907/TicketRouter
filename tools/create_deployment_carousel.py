from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project")
ASSETS = ROOT / "docs" / "assets"
OUT_DIR = ROOT / "output" / "pdf"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = OUT_DIR / "TicketRouter_Deployment_Carousel.pdf"
POST_PATH = OUT_DIR / "TicketRouter_Deployment_LinkedIn_Post.txt"

W, H = 1080, 1350
NAVY = colors.HexColor("#0f172a")
INK = colors.HexColor("#111827")
SLATE = colors.HexColor("#475569")
MUTED = colors.HexColor("#94a3b8")
BLUE = colors.HexColor("#2563eb")
LIGHT_BLUE = colors.HexColor("#dbeafe")
GREEN = colors.HexColor("#16a34a")
LIGHT_GREEN = colors.HexColor("#dcfce7")
ORANGE = colors.HexColor("#f97316")
LIGHT_ORANGE = colors.HexColor("#ffedd5")
BG = colors.HexColor("#f8fafc")
WHITE = colors.white
BORDER = colors.HexColor("#e2e8f0")


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


def draw_wrapped(c, text, x, y, max_width, font="Helvetica", size=28, color=SLATE, leading=None):
    c.setFont(font, size)
    c.setFillColor(color)
    leading = leading or size * 1.25
    for line in wrap_text(text, font, size, max_width):
        c.drawString(x, y, line)
        y -= leading
    return y


def title(c, text, y=1180, size=58):
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", size)
    for line in wrap_text(text, "Helvetica-Bold", size, W - 144):
        c.drawString(72, y, line)
        y -= size * 1.05
    return y


def pill(c, text, x, y, w, h, fill, text_color=NAVY, stroke=None, size=21):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", size)
    c.drawCentredString(x + w / 2, y + h / 2 - size * 0.35, text)


def image_box(c, image_name, x, y, w, h, radius=18):
    path = ASSETS / image_name
    img = Image.open(path).convert("RGB")
    iw, ih = img.size
    scale = min(w / iw, h / ih)
    nw, nh = iw * scale, ih * scale
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.drawImage(ImageReader(img), x + (w - nw) / 2, y + (h - nh) / 2, nw, nh, preserveAspectRatio=True)


def page(c, n):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 18)
    c.drawString(72, 54, "TicketRouter deployment story")
    c.drawRightString(W - 72, 54, f"{n}/5")


def metric(c, label, value, x, y, color=BLUE):
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER)
    c.roundRect(x, y, 285, 120, 18, fill=1, stroke=1)
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 20)
    c.drawString(x + 24, y + 78, label)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 38)
    c.drawString(x + 24, y + 30, value)


def make_pdf():
    c = canvas.Canvas(str(PDF_PATH), pagesize=(W, H))

    # Slide 1
    page(c, 1)
    pill(c, "Deployed ML Project", 72, 1238, 245, 48, LIGHT_BLUE, text_color=BLUE)
    y = title(c, "I deployed my fine-tuned ticket router on Cloud Run", 1138, 58)
    draw_wrapped(
        c,
        "TicketRouter is a Qwen3-1.7B + LoRA model served through a containerized FastAPI endpoint.",
        72,
        y - 22,
        880,
        size=30,
    )
    image_box(c, "cloudrun-root.png", 72, 340, 936, 520)
    pill(c, "Live API", 72, 278, 150, 54, LIGHT_GREEN, text_color=GREEN)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(245, 292, "Public Cloud Run endpoint with service metadata")
    c.showPage()

    # Slide 2
    page(c, 2)
    title(c, "The deployment path mattered as much as the model score.", 1160, 52)
    draw_wrapped(
        c,
        "The goal was not to stop at a notebook. I wanted a small production-shaped service that could accept tickets and return routing decisions.",
        72,
        970,
        860,
        size=29,
    )
    steps = [
        ("Qwen3-1.7B + LoRA", "Run 2 model artifact"),
        ("FastAPI", "health and route endpoints"),
        ("Docker", "repeatable container image"),
        ("Artifact Registry", "versioned image storage"),
        ("Cloud Run", "public serverless API"),
    ]
    y = 770
    for i, (name, detail) in enumerate(steps, start=1):
        c.setFillColor(WHITE)
        c.setStrokeColor(BORDER)
        c.roundRect(92, y - 10, 895, 96, 18, fill=1, stroke=1)
        pill(c, str(i), 118, y + 15, 52, 52, LIGHT_BLUE, text_color=BLUE, size=23)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 27)
        c.drawString(200, y + 45, name)
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 23)
        c.drawString(200, y + 12, detail)
        y -= 122
    c.showPage()

    # Slide 3
    page(c, 3)
    title(c, "The API exposes the exact proof points I need for a demo.", 1165, 50)
    draw_wrapped(c, "A simple service contract keeps the demo honest: status, health, and inference.", 72, 1000, 880, size=29)
    image_box(c, "cloudrun-health.png", 72, 665, 430, 245)
    c.setFillColor(WHITE)
    c.setStrokeColor(BORDER)
    c.roundRect(548, 665, 460, 245, 18, fill=1, stroke=1)
    c.setFillColor(colors.HexColor("#111111"))
    c.roundRect(572, 675, 412, 196, 10, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#e5e7eb"))
    c.setFont("Courier-Bold", 20)
    c.drawString(594, 826, "POST /route")
    c.setFont("Courier", 17)
    c.drawString(594, 790, "predicted_label: O365")
    c.drawString(594, 758, "final_route: O365")
    c.drawString(594, 726, "confidence: 0.9964")
    c.drawString(594, 700, "action: Auto-route")
    pill(c, "GET /health", 116, 590, 190, 54, LIGHT_BLUE, text_color=BLUE)
    pill(c, "POST /route", 616, 590, 190, 54, LIGHT_GREEN, text_color=GREEN)
    draw_wrapped(
        c,
        "The route endpoint sends an Outlook and Teams ticket to the model and returns O365 with confidence and an auto-route action.",
        72,
        440,
        895,
        size=30,
        color=INK,
    )
    c.showPage()

    # Slide 4
    page(c, 4)
    title(c, "The deployed service is backed by controlled fine-tuning results.", 1160, 50)
    metric(c, "Baseline", "24.8%", 72, 930, color=ORANGE)
    metric(c, "Run 2", "77.8%", 398, 930, color=GREEN)
    metric(c, "Macro F1", "0.753", 724, 930, color=BLUE)
    image_box(c, "ops-console-run2.png", 72, 270, 936, 560)
    draw_wrapped(
        c,
        "Run 2 won across four experiments and became the production candidate.",
        72,
        205,
        850,
        size=28,
        color=SLATE,
    )
    c.showPage()

    # Slide 5
    page(c, 5)
    title(c, "What made it production-minded: constraints, fallback, and honesty.", 1160, 48)
    image_box(c, "confusion-matrix-run2.png", 72, 540, 505, 520)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 35)
    c.drawString(625, 960, "Deployment notes")
    notes = [
        "CPU Cloud Run demo is live and public.",
        "NVIDIA L4 GPU config was prepared, but quota limited execution.",
        "Low-confidence tickets route to human review.",
        "Active Directory remains the weakest class and needs better labeled data.",
    ]
    y = 885
    for note in notes:
        c.setFillColor(WHITE)
        c.setStrokeColor(BORDER)
        c.roundRect(610, y - 18, 380, 74, 14, fill=1, stroke=1)
        draw_wrapped(c, note, 632, y + 18, 330, size=21, color=INK)
        y -= 98
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 34)
    c.drawString(72, 365, "Takeaway")
    draw_wrapped(
        c,
        "A useful AI project is not just a model. It is a service with clear evaluation, known failure modes, and a deployment path.",
        72,
        315,
        880,
        size=30,
        color=SLATE,
    )
    c.showPage()

    c.save()


POST_TEXT = """I turned my Week 5 fine-tuning project into a deployed model-serving API.

TicketRouter routes messy IT support tickets into resolver queues using a Qwen3-1.7B model fine-tuned with LoRA.

The model work mattered, but the part I wanted to push further was deployment:

- FastAPI inference service
- Dockerized model-serving container
- Artifact Registry image
- Google Cloud Run public endpoint
- /health endpoint for service status
- /route endpoint for ticket classification
- confidence gate for human review

The best fine-tuned run improved validation accuracy from 24.8% to 77.8%, with macro F1 reaching 0.753.

I also learned the less glamorous but more useful lesson: deployment constraints are real. I prepared the Cloud Run NVIDIA L4 GPU path, but project quota limited GPU execution, so the public demo runs CPU-only. Slower first request, but the end-to-end deployment path works.

The biggest model weakness is still Active Directory. Ambiguous access tickets can look like O365 or Fileservice. That is why the service includes a human-review fallback instead of pretending every prediction is production-safe.

This became more than a notebook: model selection, failure analysis, Docker, Cloud Run, and a live API.

Curious how others are handling deployment constraints when taking fine-tuned models from notebook to demo.

#MachineLearning #MLOps #CloudRun #FastAPI #Docker #LLM #FineTuning #AIEngineering #HuggingFace
"""


if __name__ == "__main__":
    make_pdf()
    POST_PATH.write_text(POST_TEXT, encoding="utf-8")
    print(PDF_PATH)
    print(POST_PATH)
