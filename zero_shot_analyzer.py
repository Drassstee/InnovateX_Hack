# Твой файл: image_classification.py (версия Zero-Shot)

import argparse
import json

import cv2
from transformers import pipeline
import warnings
from PIL import Image

# Подавляем "шум"
warnings.filterwarnings("ignore")

# python zero_shot_analyzer.py --image test_images/guitar_only.png --labels "acoustic guitar,guitar strap,wooden floor,cat"

def calculate_iou(box1, box2):
    """
    Рассчитывает IoU (Intersection over Union) для двух боксов.
    Формат боксов: {'xmin', 'ymin', 'xmax', 'ymax'}
    """
    # 1. Найти координаты пересечения
    x_left = max(box1['xmin'], box2['xmin'])
    y_top = max(box1['ymin'], box2['ymin'])
    x_right = min(box1['xmax'], box2['xmax'])
    y_bottom = min(box1['ymax'], box2['ymax'])

    # Если боксы не пересекаются
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # 2. Вычислить площадь пересечения
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # 3. Вычислить площади каждого бокса
    box1_area = (box1['xmax'] - box1['xmin']) * (box1['ymax'] - box1['ymin'])
    box2_area = (box2['xmax'] - box2['xmin']) * (box2['ymax'] - box2['ymin'])

    # 4. Вычислить площадь объединения (Area1 + Area2 - Intersection)
    union_area = box1_area + box2_area - intersection_area

    if union_area == 0:
        return 0.0

    # 5. Рассчитать IoU
    iou = intersection_area / union_area
    return iou


def non_maximum_suppression(results_list, iou_threshold):
    """
    Применяет Non-Maximum Suppression (NMS) к списку результатов.
    """
    # 1. Сортируем все боксы по 'score' (от лучшего к худшему)
    sorted_results = sorted(results_list, key=lambda x: x['score'], reverse=True)

    final_boxes = []

    while sorted_results:
        # 2. Берем лучший бокс из списка и ОБЯЗАТЕЛЬНО добавляем его в ответ
        best_box = sorted_results.pop(0)
        final_boxes.append(best_box)

        # 3. Теперь проверяем оставшиеся боксы
        boxes_to_keep = []
        for box in sorted_results:
            # 4. Считаем, насколько этот бокс "похож" на наш лучший
            iou = calculate_iou(best_box['box'], box['box'])

            # 5. Если они НЕ СИЛЬНО пересекаются (iou < порога),
            # то это, вероятно, ДРУГОЙ объект. Оставляем его для след. раунда.
            if iou < iou_threshold:
                boxes_to_keep.append(box)

        # 6. Наш новый список для проверки — это только те, что мы "оставили"
        sorted_results = boxes_to_keep

    return final_boxes


def run_analysis(image_path, candidate_labels):
    """
    Главная ML-функция (теперь с "закрученными" фильтрами).
    """
    try:
        # 1. Загружаем модель
        print("Загружаю модель Zero-Shot (Grounding DINO)...")
        detector = pipeline("zero-shot-object-detection", model="IDEA-Research/grounding-dino-base")

        # 2. Анализируем картинку
        print(f"Анализирую {image_path} на наличие: {candidate_labels}")
        results = detector(image_path, candidate_labels=candidate_labels)

        # --- Получаем РАЗМЕР картинки ---
        try:
            img = Image.open(image_path)
            img_width, img_height = img.size
            total_image_area = float(img_width * img_height)
        except Exception as e:
            return {"status": "error", "message": f"Не могу прочитать размер картинки: {e}"}

        # ❗️❗️--- НАЧАЛО "УМНОГО ФИЛЬТРА" (v2) ---❗️❗️

        # --- Этап 1: "Грубый" фильтр по Уверенности ---
        # Поднимаем порог с 10% до 15%
        MIN_CONFIDENCE = 0.0  # 👈 ИЗМЕНЕНИЕ

        pre_filtered_results = []
        for item in results:
            if item['score'] > MIN_CONFIDENCE:
                item['score'] = round(item['score'], 4)
                pre_filtered_results.append(item)

        # --- Этап 2: "Грубый" фильтр по РАЗМЕРУ ---
        # "Затягиваем" максимальный размер с 50% до 25%
        MIN_AREA_RATIO = 0.01  # 1%
        MAX_AREA_RATIO = 0.5  # 25% 👈 ИЗМЕНЕНИЕ

        size_filtered_results = []
        for item in pre_filtered_results:
            box = item['box']
            box_area = (box['xmax'] - box['xmin']) * (box['ymax'] - box['ymin'])
            area_ratio = box_area / total_image_area

            if (area_ratio > MIN_AREA_RATIO) and (area_ratio < MAX_AREA_RATIO):
                size_filtered_results.append(item)

        # --- Этап 3: "Тонкий" фильтр NMS (убираем дубликаты) ---
        IOU_THRESHOLD = 0.9

        formatted_results = non_maximum_suppression(size_filtered_results, IOU_THRESHOLD)

        # ❗️❗️--- КОНЕЦ "УМНОГО ФИЛЬТРА" (v2) ---❗️❗️

        # 4. Возвращаем УСПЕШНЫЙ словарь
        return {"status": "success", "data": formatted_results}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Это точка входа в твой скрипт ---
if __name__ == "__main__":
    # 6. Настраиваем чтение ДВУХ аргументов
    parser = argparse.ArgumentParser(description="Zero-Shot анализатор изображений")
    parser.add_argument("--image", type=str, required=True, help="Путь к файлу с изображением")

    # Новый аргумент!
    parser.add_argument("--labels", type=str, required=True,
                        help="Что искать? Метки через запятую. Пример: 'гитара,ремень'")

    args = parser.parse_args()

    # 7. Превращаем строку "гитара,ремень" в список ['гитара', 'ремень']
    labels_list = [label.strip() for label in args.labels.split(',')]

    # 8. Запускаем анализ
    final_output = run_analysis(args.image, labels_list)

    # 9. Печатаем финальный JSON
    print(json.dumps(final_output, indent=2))