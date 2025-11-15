# Твой файл: florence_analyzer.py (Microsoft Florence-2)

import argparse
import json
import warnings
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
import torch  # Florence-2 требует PyTorch

# --- Подавляем "шум" ---
warnings.filterwarnings("ignore", category=UserWarning)


# --- 1. ЗАГРУЗЧИКИ МОДЕЛЕЙ ---
def load_models():
    """
    Загружает Florence-2 (модель и процессор).
    """
    print("Загружаю модель Florence-2 (microsoft/florence-2-large)...")
    # Эта модель "тяжелая" (~2.2 ГБ)
    model_id = 'microsoft/florence-2-large'

    # Модель "думает", что она на CUDA, но мы "обманем" ее
    # (Это нужно для твоего M1 `mps`)
    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

    # --- Попытка "включить" твой M1 `mps` ---
    # PyTorch должен "подхватить" твой mps
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)
    print(f"--- Модель Florence-2 загружена на: {device} ---")

    return model, processor, device


# --- 2. "МОЗГ" (Здесь все в одной функции) ---
def run_analysis(model, processor, device, image_path, labels_to_find):
    """
    Главная "думающая" функция для Florence-2.
    """
    print(f"Анализирую {image_path} на наличие: {labels_to_find}")

    # 1. Готовим "приказ" (task prompt)
    # Мы "приказываем" модели: "Найди объекты"
    # И "говорим" ей, какие именно
    task_prompt = "<OD>"  # OD = Object Detection
    # Мы "оборачиваем" наши метки в спец. теги
    text_prompt = f"a {labels_to_find[0]}"  # (Пока для простоты берем 1 метку)

    try:
        # 2. Открываем картинку
        image = Image.open(image_path)

        # 3. "Просим" модель "подумать"
        inputs = processor(text=task_prompt, images=image, return_tensors="pt")

        # Перемещаем "данные" на тот же `device` (mps/cpu), что и "модель"
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # 4. Генерируем "ответ"
        # `max_new_tokens=1000` - даем ей "место" для ответа
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            num_beams=3,
        )

        # 5. "Расшифровываем" ответ
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        # 6. "Парсим" (разбираем) ответ модели
        # Florence-2 "отвечает" текстом, который нужно "разобрать"
        # Ответ выглядит как: '<OD> a door <box_222_333_444_555>'
        # Нам нужно "вытащить" 'label' и 'box'

        # `post_process_generation` - это "секретная" функция из `processor`
        results = processor.post_process_generation(generated_text, task=task_prompt,
                                                    image_size=(image.width, image.height))

        # 7. Форматируем в наш "фирменный" JSON
        # Результат `results` - это {'<OD>': {'bboxes': [[...]], 'labels': [...]}}

        formatted_results = []
        if task_prompt in results:
            bboxes = results[task_prompt].get('bboxes', [])
            labels = results[task_prompt].get('labels', [])

            # (Florence-2 не дает 'score', а просто 'уверенно' отвечает)
            for box, label in zip(bboxes, labels):
                formatted_results.append({
                    "score": 1.0,  # (Ставим 1.0, т.к. она не "оценивает")
                    "label": label,
                    "box": {
                        'xmin': int(box[0]),
                        'ymin': int(box[1]),
                        'xmax': int(box[2]),
                        'ymax': int(box[3])
                    }
                })

        return {"status": "success", "data": formatted_results}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- 3. "ДИРИЖЕР" (Точка входа) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Florence-2 'SOTA' Analyzer")
    parser.add_argument("--image", type=str, required=True, help="Путь к изображению")
    parser.add_argument("--labels", type=str, required=True,
                        help="Что искать? (Пока только 1 метка, напр: 'a door')")

    args = parser.parse_args()

    # (Этот код пока "простой" и берет 1 метку, напр: 'door')
    labels_list = [label.strip() for label in args.labels.split(',')]

    # 1. Загружаем модели (1 раз)
    model, processor, device = load_models()

    # 2. Запускаем анализ
    final_output = run_analysis(model, processor, device, args.image, labels_list)

    # 3. Печатаем JSON
    print(json.dumps(final_output, indent=2))