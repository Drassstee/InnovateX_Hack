# Файл: qr_detector.py

import cv2
import argparse
import json
import warnings


def find_qr_codes(image_path):
    """
    Ищет и декодирует QR-коды на картинке с помощью OpenCV
    """
    print(f"Ищу QR-коды на {image_path}...")

    # 1. Загружаем картинку
    image = cv2.imread(image_path)
    if image is None:
        return {"status": "error", "message": "Не могу загрузить картинку"}

    # 2. Инициализируем "магию" OpenCV
    detector = cv2.QRCodeDetector()

    # 3. Ищем и "читаем" QR-коды
    # data - это "прочитанный" текст (напр, URL)
    # bbox - это 4 точки (полигон)
    # straight_qrcode - это "выпрямленное" изображение QR-кода
    data, bbox, straight_qrcode = detector.detectAndDecode(image)

    formatted_results = []

    # 4. Проверяем, что-то нашли?
    if bbox is not None and data is not None:
        # data может быть одним URL или списком, если QR-кодов много
        # Превращаем в список, чтобы было "гибко"
        if not isinstance(data, (list, tuple)):
            data_list = [data]
            bbox_list = [bbox]
        else:
            data_list = list(data)
            bbox_list = list(bbox)

        print(f"Найдено {len(data_list)} QR-кодов.")

        for text, box in zip(data_list, bbox_list):
            # "Лечим" numpy-типы (мы это уже делали)
            cleaned_box = [[int(coord[0]), int(coord[1])] for coord in box]

            formatted_results.append({
                "text": text,  # "Прочитанный" URL
                "box": cleaned_box
            })

    return {"status": "success", "data": formatted_results}


# --- "ДИРИЖЕР" ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenCV QR-Code Детектор")
    parser.add_argument("--image", type=str, required=True, help="Путь к PNG документа")
    args = parser.parse_args()

    final_output = find_qr_codes(args.image)

    print(json.dumps(final_output, indent=2))