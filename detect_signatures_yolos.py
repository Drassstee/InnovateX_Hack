from transformers import pipeline
from PIL import Image
import os

INPUT_FOLDER = "test_images"
OUTPUT_FOLDER = "results_yolos"
CONF_THRESHOLD = 0.5

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load the YOLOS signature detector
yolos = pipeline(
    task="object-detection",
    model="mdefrance/yolos-small-signature-detection",
    device_map="auto",
)

for img_name in os.listdir(INPUT_FOLDER):
    img_path = os.path.join(INPUT_FOLDER, img_name)

    if os.path.isdir(img_path):
        continue  # avoid folders

    img = Image.open(img_path).convert("RGB")

    preds = yolos(img)

    # Draw boxes manually using PIL
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)

    for p in preds:
        score = p["score"]
        if score < CONF_THRESHOLD:
            continue

        box = p["box"]
        x1, y1, x2, y2 = box["xmin"], box["ymin"], box["xmax"], box["ymax"]

        draw.rectangle((x1, y1, x2, y2), outline="green", width=3)
        draw.text((x1, y1 - 10), f"signature {score:.2f}", fill="green")

    img.save(os.path.join(OUTPUT_FOLDER, img_name))

print("YOLOS signature detections saved to:", OUTPUT_FOLDER)
