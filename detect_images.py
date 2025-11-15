from ultralytics import YOLO
import cv2
import os
from pathlib import Path

CONF_THRESHOLD = 0.5  # Minimum confidence allowed


def main():
    model_path = Path("runs/detect/train8/weights/best.pt")
    test_images = Path("dataset/images/test")
    output_folder = Path("runs/detect/predict_custom")

    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return

    if not test_images.exists():
        print(f"Test images folder not found: {test_images}")
        return

    print(f"Loading model: {model_path}")
    model = YOLO(str(model_path))

    output_folder.mkdir(parents=True, exist_ok=True)

    print(f"Running inference on: {test_images}")

    for img_name in os.listdir(test_images):
        img_path = test_images / img_name

        results = model(img_path)
        img = cv2.imread(str(img_path))

        for r in results:
            for box in r.boxes:
                conf = float(box.conf)
                cls = int(box.cls)

                if conf < CONF_THRESHOLD:
                    continue  # Skip weak detections

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = f"{model.names[cls]} {conf:.2f}"

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    img,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        cv2.imwrite(str(output_folder / img_name), img)

    print(f"Done. Results saved in: {output_folder}")


if __name__ == "__main__":
    main()
