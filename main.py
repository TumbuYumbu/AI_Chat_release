import google.generativeai as genai
import json
import os
from gui_chat_interface import ChatInterface

# Путь к файлу конфигурации
file_path = r'C:\Temp\Special\config.json'

def configure_api():
    """
    Настройка API Gemini.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    with open(file_path, 'r') as file:
        config = json.load(file)

    # Читаем API ключ из конфигурации
    api_key = config.get("PVY_GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API ключ не найден в конфигурации!")

    # Настройка API
    genai.configure(api_key=api_key)

def main():
    """
    Главная функция запуска.
    """
    try:
        # Настраиваем API
        configure_api()

        # Запускаем GUI
        app = ChatInterface()
        app.run()

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
