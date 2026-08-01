from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "output/pdf/rendered_pages"
out = ROOT / "output/pdf/contact_sheets"
out.mkdir(parents=True, exist_ok=True)
for group in ["mathematical", "software", "supplement"]:
    pages = sorted(source.glob(group + "-*.png"))
    thumbs = []
    for index, page in enumerate(pages, 1):
        image = Image.open(page).convert("RGB")
        image.thumbnail((240, 320))
        canvas = Image.new("RGB", (260, 350), "white")
        canvas.paste(image, ((260 - image.width)//2, 20))
        ImageDraw.Draw(canvas).text((10, 5), f"{group} {index}", fill="black")
        thumbs.append(canvas)
    cols = 5
    sheet = Image.new("RGB", (cols * 260, ((len(thumbs) + cols - 1)//cols) * 350), "#dddddd")
    for index, image in enumerate(thumbs): sheet.paste(image, ((index % cols)*260, (index // cols)*350))
    sheet.save(out / f"{group}.png")
