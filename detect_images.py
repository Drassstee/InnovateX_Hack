from ultralytics import YOLO
from pathlib import Path

def main():
    model_path = Path("runs/detect/train8/weights/best.pt")
    test_images = Path("dataset/images/test")

    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return

    if not test_images.exists():
        print(f"Test images folder not found: {test_images}")
        return

    print(f"Loading model: {model_path}")
    model = YOLO(str(model_path))

    print(f"Running inference on folder: {test_images}")

    model.predict(
        source=str(test_images),
        imgsz=768,
        save=True,
        save_txt=False,
        project="runs/detect",
        name="predict",
        exist_ok=False
    )

    print("Finished. Check results in runs/detect/predict")


if __name__ == "__main__":
    main()
