from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


pdf_path = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project\output\pdf\TicketRouter_LinkedIn_Carousel.pdf")
out_dir = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project\tmp\linkedin_carousel\rendered")
out_dir.mkdir(parents=True, exist_ok=True)

pdf = pdfium.PdfDocument(str(pdf_path))
pages = []
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.3)
    image = bitmap.to_pil().convert("RGB")
    path = out_dir / f"page-{i + 1}.png"
    image.save(path)
    pages.append(path)

thumb = 300
cols = 4
rows = 2
sheet = Image.new("RGB", (cols * thumb, rows * (thumb + 35)), "white")
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(pages):
    image = Image.open(path).convert("RGB")
    image.thumbnail((thumb - 20, thumb - 20))
    x = (i % cols) * thumb + 10
    y = (i // cols) * (thumb + 35) + 28
    sheet.paste(image, (x, y))
    draw.text((x, y - 22), f"Page {i + 1}", fill=(15, 23, 42))

contact = out_dir / "carousel_contact_sheet.png"
sheet.save(contact)
print(contact)
