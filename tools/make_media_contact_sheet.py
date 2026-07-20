from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


media = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project\tmp\linkedin_carousel\media")
out = Path(r"C:\Users\navni\OneDrive\Documents\Week 5 Project\tmp\linkedin_carousel\media_contact_sheet.png")

thumb_w, thumb_h = 360, 220
cols = 2
files = sorted(media.iterdir())
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 40)), "white")
draw = ImageDraw.Draw(sheet)

for index, path in enumerate(files):
    image = Image.open(path).convert("RGB")
    image.thumbnail((thumb_w - 20, thumb_h - 20))
    x = (index % cols) * thumb_w + 10
    y = (index // cols) * (thumb_h + 40) + 30
    sheet.paste(image, (x, y))
    draw.text((x, y - 24), f"{path.name} {Image.open(path).size}", fill=(20, 30, 45))

sheet.save(out)
print(out)
