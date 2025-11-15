# Твой файл: text_recognizer.py

import easyocr
import argparse
import json
import warnings

# Подавляем "шум" от EasyOCR
warnings.filterwarnings("ignore", category=UserWarning)


def run_ocr(image_path):
    # python text_recognizer.py --image test_images/screenshot.png
    """
    Главная OCR-функция.
    Принимает путь к картинке, возвращает словарь с результатом.
    """
    try:
        # 1. Загружаем "читалку".
        # ['en'] - ищем английский язык. Можно добавить ['en', 'ru']
        # gpu=True - используем GPU (твой mps)
        print("Загружаю модель OCR...")
        reader = easyocr.Reader(['ru'], gpu=True)


        # 2. "Читаем" весь текст с картинки
        print(f"Распознаю текст на {image_path}...")
        # results - это список вида: [ (box, text, confidence), ... ]
        results = reader.readtext(image_path)

        # 3. Форматируем результат в УДОБНЫЙ JSON
        formatted_results = []
        for (bbox, text, prob) in results:
            # easyocr отдает box в виде [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            # Это 4 точки (полигон). Он чуть сложнее, чем наш [xmin, ymin, xmax, ymax],
            # но он ТОЧНЕЕ, если текст, например, повернут.
            cleaned_bbox = [[int(coord) for coord in point] for point in bbox]

            formatted_results.append({
                "text": text,
                "confidence": round(float(prob), 4),
                "box": cleaned_bbox
            })

        # 4. Возвращаем УСПЕШНЫЙ словарь
        return {"status": "success", "data": formatted_results}

    except Exception as e:
        # 5. Возвращаем ОШИБКУ
        return {"status": "error", "message": str(e)}


# --- Это точка входа в твой скрипт ---
if __name__ == "__main__":
    # 6. Настраиваем чтение аргумента --image
    parser = argparse.ArgumentParser(description="Распознаватель текста (OCR) для хакатона")
    parser.add_argument("--image", type=str, required=True, help="Путь к файлу с изображением")
    args = parser.parse_args()

    # 7. Запускаем анализ
    final_output = run_ocr(args.image)

    # 8. Печатаем финальный JSON в консоль
    # Стало:
    print(json.dumps(final_output, indent=2, ensure_ascii=False))