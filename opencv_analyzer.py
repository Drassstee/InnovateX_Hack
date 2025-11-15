# Твой файл: opencv_analyzer.py

import cv2
import numpy as np
import argparse
import json
import warnings

# --- Подавляем "шум" ---
warnings.filterwarnings("ignore", category=UserWarning)


def find_lines(edges_image):
    """
    Ищет ВСЕ линии на "карте краев" (Canny)
    """
    print("Ищу линии (стены)...")

    # --- TODO: "Магические числа" для хакатона ---
    # Это "настройки", которые тебе придется "подкрутить"
    # завтра, когда увидишь РЕАЛЬНЫЕ чертежи.

    # (rho, theta) - не трогай
    rho_resolution = 1
    theta_resolution = np.pi / 180

    # threshold - "Сколько 'голосов' нужно линии, чтобы мы ее засчитали?"
    # (Чем > число, тем "жестче" отбор)
    line_threshold = 100

    # minLineLength - "Игнорируй линии короче X пикселей"
    # (Идеально, чтобы "убить" мелкий "шум" - текст, штриховку)
    min_line_length = 200

    # maxLineGap - "Если 2 линии 'почти' касаются (разрыв < X), 'склей' их"
    max_line_gap = 10
    # --- Конец "Магических чисел" ---

    lines = cv2.HoughLinesP(
        edges_image,
        rho_resolution,
        theta_resolution,
        line_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap
    )

    formatted_lines = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # "Лечим" ошибку JSON (превращаем numpy.int32 в int)
            formatted_lines.append({
                "x1": int(x1),
                "y1": int(y1),
                "x2": int(x2),
                "y2": int(y2)
            })

    print(f"Найдено {len(formatted_lines)} линий.")
    return formatted_lines


def find_circles(gray_image):
    """
    Ищет ВСЕ круги на Ч/Б картинке
    """
    print("Ищу круги (символы, розетки)...")

    # --- TODO: "Магические числа" для хакатона ---
    # "Подкрути" их, чтобы найти то, что нужно

    # minDist - "Мин. дистанция между центрами кругов"
    # (Защита от "галлюцинаций", когда 1 круг = 20 детектов)
    min_dist = 20

    # param1 (Canny) и param2 (Accumulator) - главные "крутилки"
    # (Поиграй с param2: < 30 = больше "шума", > 50 = "пропустит" нечеткие)
    param1 = 50
    param2 = 30

    # minRadius/maxRadius - "Фильтр по размеру"
    # (Идеально, чтобы найти "символы", но "игнорировать" круглые столы)
    min_radius = 12
    max_radius = 35
    # --- Конец "Магических чисел" ---

    circles = cv2.HoughCircles(
        gray_image,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=min_dist,
        param1=param1,
        param2=param2,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    formatted_circles = []
    if circles is not None:
        # "Округляем" и "лечим" numpy-типы
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            formatted_circles.append({
                "x": int(x),
                "y": int(y),
                "radius": int(r)
            })

    print(f"Найдено {len(formatted_circles)} кругов.")
    return formatted_circles


# --- "ДИРИЖЕР" ---
def main():
    parser = argparse.ArgumentParser(description="OpenCV 'Геометрический' Анализатор")
    parser.add_argument("--image", type=str, required=True, help="Путь к PNG чертежа")
    args = parser.parse_args()

    # 1. Загружаем картинку
    image = cv2.imread(args.image)
    if image is None:
        print(f"Ошибка: Не могу загрузить картинку {args.image}")
        return

    # 2. "Пре-процессинг"
    # (OpenCV "любит" Ч/Б и "края")
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges_image = cv2.Canny(gray_image, 50, 150)  # (50, 150 - тоже "магия")

    # 3. Выполняем CV-задачи
    lines_list = find_lines(edges_image)
    circles_list = find_circles(gray_image)  # (Круги ищем на Ч/Б, не на "краях")

    # 4. Формируем финальный JSON-ответ
    final_output = {
        "status": "success",
        "image_path": args.image,
        "geometry": {
            "lines": lines_list,
            "circles": circles_list
        }
    }

    # 5. Печатаем JSON в stdout
    print(json.dumps(final_output, indent=2))


if __name__ == "__main__":
    main()