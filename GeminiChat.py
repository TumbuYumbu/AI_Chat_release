import google.generativeai as genai
from google.generativeai import GenerativeModel, GenerationConfig
import json
import os
from tkinter import messagebox

# Единые настройки генерации AI-модели
generation_config = GenerationConfig(
    temperature=0.5,
    max_output_tokens=2000
)

# Задаём название для тюнингованной модели, его можно менять на своё
custom_model_id = "new-custom-chat-assistant"

# Единые настройки безопасности AI-модели
safety_settings = [
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": 3},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": 3},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": 3},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": 4},
]

# Глобальный кэш для используемой модели
_model_cache = None

# Конфигурация API
file_path = r'C:\Temp\Special\config.json'

# Чтение API ключа и настройка API
def configure_api():
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, 'r') as file:
        config = json.load(file)

    api_key = config.get("PVY_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API ключ не найден")

    genai.configure(api_key=api_key)


_model_cache = None  # глобальный кэш


def get_model_instance():
    global _model_cache
    if _model_cache:
        return _model_cache  # если кэш уже есть — не ищем заново

    # По умолчанию — стандартная модель
    target_model = "gemini-1.5-flash"

    # Попробуем найти тюнингованную, если она была создана
    preferred_id = custom_model_id
    tuned_models = genai.list_tuned_models()
    found = [m.name for m in tuned_models if m.name.endswith(preferred_id)]
    if found:
        target_model = found[0]  # переопределим, если нашли

    # Нельзя передавать system_instruction для тюнингов
    kwargs = {
        "model_name": target_model,
        "generation_config": generation_config,
        "safety_settings": safety_settings
    }
    # В названиях тюннингованых моделей есть префикс tunedModels
    if "tunedModels/" not in target_model:
        kwargs["system_instruction"] = (
            "Отвечай как консультант, строго в образовательных целях. "
            "Ты не заменяешь врача, а являешься учителем. "
            "Отвечай всегда на русском."
        )

    print(f"[DEBUG] Используется модель: {target_model}")

    _model_cache = genai.GenerativeModel(**kwargs)
    return _model_cache


# Функция для обработки запросов с использованием модели
def generate_response(query, mode="chat", chat_session=None, cot_mode=False):
    """
    Генерирует ответ на запрос пользователя.

    :param query: Запрос пользователя.
    :param mode: Режим работы ("chat", "no_memory").
    :param chat_session: Объект ChatSession для диалога (если режим "chat").
    :param cot_mode: Режим Chain-of-Thought (анализируется ответ трёх моделей).
    :return: Ответ модели.
    """

    # получим текущую модель
    model = get_model_instance()

    if mode == "chat":
        # Работа через ChatSession
        if cot_mode:    # учтём вероятность включения режима Chain-of-Thought
            responses = []

            for _ in range(3):
                # Клонируем чат с историей (если есть), чтобы каждый ответ был изолирован
                temp_chat = model.start_chat(history=chat_session.history if chat_session else None)
                resp = temp_chat.send_message(query)
                responses.append(resp.text)

                # Выбираем наиболее частый ответ
            selected = max(set(responses), key=responses.count)

            if not chat_session:
                chat_session = model.start_chat()

            # Добавляем один раз запрос и выбранный ответ в чат-историю
            chat_session.send_message(query)
            chat_session.send_message(selected)

            return selected, chat_session

        else:
            if not chat_session:
                chat_session = model.start_chat()
            response = chat_session.send_message(query)
            return response.text, chat_session

    elif mode == "no_memory":
        # Работа через односторонний запрос
        response = model.generate_content(query)
        return response.text, None

    else:
        raise ValueError(f"Неверный режим: {mode}")


def train_model_from_blocks(blocks):
    """
    Обучает новую тюнингованную модель на переданных блоках.
    :param blocks: список словарей с ключами "text_input" и "output"
    """
    if not blocks:
        print("🚫 Нет данных для обучения.")
        return


    # Проверка существующей модели

    existing_model = next((m for m in genai.list_tuned_models() if m.name.endswith(custom_model_id)), None)
    if existing_model:
        user_choice = messagebox.askyesno("Переобучение модели",
            f"Модель '{custom_model_id}' уже существует.\nУдалить и обучить заново?")
        if not user_choice:
            return
        try:
            genai.delete_tuned_model(existing_model.name)
            print(f"🗑 Удалена модель: {existing_model.name}")
        except Exception as e:
            print(f"❌ Не удалось удалить модель: {e}")
            return

    # Запуск обучения
    try:
        # Показываем окно прогресса
        print(f"🚀 Обучение на {len(blocks)} блоках...")

        batch_size = min(len(blocks), 60)

        operation = genai.create_tuned_model(
            source_model="models/gemini-1.5-flash-001-tuning",
            training_data=blocks,
            id=custom_model_id,
            display_name="Новый умный ассистент",
            description="Модель, которая обучена на пользовательском датасете",
            temperature=0.5,
            epoch_count=3,
            batch_size=batch_size
        )
        tuned_model = operation.result()
        print(f"✅ Обучение завершено: {tuned_model.name}")

        global _model_cache
        _model_cache = genai.GenerativeModel(
            model_name=tuned_model.name,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print(f"💾 Новая модель {tuned_model.name} установлена и будет использоваться по умолчанию.")

         # --- После обучения: тестируем модель ---
        print("\n📊 Проверка модели на обучающих примерах:")
        test_model = genai.GenerativeModel(model_name=tuned_model.name)
        test_chat = test_model.start_chat()
        for i, example in enumerate(blocks, 1):
            question = example["text_input"]
            expected = example["output"]
            try:
                response = test_chat.send_message(question)
                actual = response.text.strip()
                match = expected.strip() in actual
                status = "✅" if match else "❌"
                print(f"\n[{i}] Вопрос: {question}")
                print(f"     🔹 Ожидаемый: {expected}")
                print(f"     🔸 Получен: {actual}")
                print(f"     {status} {'Совпадает' if match else 'Не совпадает'}")
            except Exception as e:
                print(f"[{i}] ❌ Ошибка при тестировании: {e}")

    except Exception as e:
        print(f"❌ Ошибка при обучении: {e}")

