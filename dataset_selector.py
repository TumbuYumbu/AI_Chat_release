# dataset_selector.py - подгружаем датасет и выбираем блоки, которые
# надо передать для обучения модели
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

DATASET_PATH = "dataset.json"

def load_dataset_and_select(parent):
    """
    Загружает датасет из файла и открывает окно выбора блоков.
    Возвращает список выбранных блоков или None.
    """
    if not os.path.exists(DATASET_PATH):
        messagebox.showerror("Ошибка", f"Файл {DATASET_PATH} не найден.")
        return None

    try:
        with open(DATASET_PATH, "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить датасет:\n{e}")
        return None

    # Если датасет пустой
    if not dataset:
        messagebox.showinfo("Пусто", "В датасете нет блоков.")
        return None

    # Окно выбора
    window = tk.Toplevel(parent)
    window.title("Выбор блоков из датасета")
    window.geometry("700x500")
    window.grab_set()

    selected_vars = []
    frame = tk.Frame(window)
    frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(frame)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Чекбоксы
    for block in dataset:
        var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(scroll_frame, text=f'📝 {block["text_input"][:100]}...', variable=var, anchor="w", justify="left", wraplength=650)
        cb.pack(fill="x", padx=10, pady=5, anchor="w")
        selected_vars.append((var, block))

    # Кнопка подтверждения
    def on_confirm():
        selected_blocks = [b for v, b in selected_vars if v.get()]
        if not selected_blocks:
            messagebox.showwarning("Нет выбора", "Не выбраны блоки для обучения!")
            return
        window.selected_blocks = selected_blocks
        window.destroy()

    tk.Button(window, text="✅ Обучить на выбранных блоках", command=on_confirm).pack(pady=10)

    parent.wait_window(window)
    return getattr(window, "selected_blocks", None)
