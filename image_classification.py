# Твой файл: image_classification.py

import argparse
import json
from transformers import pipeline
import warnings

# Подавляем "шум" - лишние предупреждения
warnings.filterwarnings("ignore")


# def run_analysis(image_path):
#     """
#     Главная ML-функция.
#     Принимает путь к картинке, возвращает словарь с результатом.
#     """
#     # python image_classification.py --image test_images/guitar_only.png
#     # pip freeze > requirements.txt
#     try:
#         # 1. Загружаем модель (pipeline)
#         # Ты можешь заменить "object-detection" на "image-classification"
#         # или любую другую задачу из Hugging Face.
#         print("Загружаю модель...")  # Это сообщение увидишь только ты в терминале
#         # Стало:
#         detector = pipeline("object-detection", model="facebook/detr-resnet-101")
#
#         # 2. Анализируем картинку
#         print(f"Анализирую {image_path}...")
#         results = detector(image_path)
#
#         # 3. Форматируем результат в УДОБНЫЙ словарь
#         formatted_results = []
#         MIN_CONFIDENCE = 0.0
#         for item in results:
#             if item['score'] > MIN_CONFIDENCE:
#                 formatted_results.append({
#                     "label": item['label'],
#                     "confidence": round(item['score'], 4),
#                     "box": item['box']  # {xmin, ymin, xmax, ymax}
#                 })
#
#         # 4. Возвращаем УСПЕШНЫЙ словарь
#         return {"status": "success", "data": formatted_results}
#
#     except Exception as e:
#         # 5. Возвращаем ОШИБКУ, если что-то пошло не так
#         return {"status": "error", "message": str(e)}

def run_analysis(image_path):
    """
    Главная ML-функция (теперь для КЛАССИФИКАЦИИ).
    Принимает путь к картинке, возвращает словарь с результатом.
    """
    try:
        # 1. Загружаем модель (классификатор)
        print("Загружаю модель классификации...")
        classifier = pipeline("image-classification", model="google/vit-base-patch16-224")

        # 2. Анализируем картинку
        print(f"Анализирую {image_path}...")
        results = classifier(image_path)

        # 3. Форматируем результат (здесь НЕТ "box"!)
        # results будет [ {'label': 'acoustic guitar', 'score': 0.9}, ... ]

        # Просто берем, например, ТОП-3 догадки
        formatted_results = results[:3]

        # 4. Возвращаем УСПЕШНЫЙ словарь
        return {"status": "success", "data": formatted_results}

    except Exception as e:
        # 5. Возвращаем ОШИБКУ, если что-то пошло не так
        return {"status": "error", "message": str(e)}

# --- Это точка входа в твой скрипт ---
if __name__ == "__main__":
    # 6. Настраиваем чтение аргумента --image из командной строки
    parser = argparse.ArgumentParser(description="Анализатор изображений для хакатона")
    parser.add_argument("--image", type=str, required=True, help="Путь к файлу с изображением")
    args = parser.parse_args()

    # 7. Запускаем анализ
    final_output = run_analysis(args.image)

    # 8. ГЛАВНОЕ: Печатаем финальный JSON в консоль.
    # Бэкенд твоего капитана "прочитает" именно этот вывод.
    print(json.dumps(final_output, indent=2))