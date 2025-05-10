import json
import tkinter as tk
import tkinter.filedialog as filedialog
from tkinter import messagebox
import GeminiChat as chat_module

from dataset_selector import load_dataset_and_select
import GeminiChat

class ChatInterface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ChatGPT-like Interface")
        self.root.geometry("600x400")

        # Флаг режима работы
        self.mode = tk.StringVar(value="chat")  # По умолчанию "chat"

        self.chat_session = None

        # Добавление кнопки-иконки с выпадающим меню
        self.menu_button = tk.Menubutton(self.root, text="☰", relief="raised")
        self.menu_button.pack(anchor="ne", padx=10, pady=1)

        self.menu = tk.Menu(self.menu_button, tearoff=0)
        self.menu_button.config(menu=self.menu)

        # Выяснение списка уже тюнингованных моделей
        self.menu.add_command(label="Мои модели", command=self.show_tuned_models)

        # Загрузка датасета для тюнингования модели
        self.menu.add_command(label="Загрузить датасет", command=self.load_dataset)

        # Пункт меню "Ассистенты"
        self.menu.add_command(label="Ассистенты", command=self.select_assistant)

        # Пункт меню "Очистить текущий чат"
        self.menu.add_command(label="Очистить текущий чат", command=self.clear_chat)

        # Верхнее поле вывода (нередактируемое)
        self.response_field = tk.Text(self.root, height=15, wrap="word", state="disabled")
        self.response_field.pack(padx=10, pady=1, fill="both", expand=True)

        # Добавляем контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.copy_text)
        self.context_menu.add_command(label="Цитировать", command=self.quote_text)

        # Привязываем контекстное меню к полю вывода
        self.response_field.bind("<Button-3>", self.show_context_menu)
        self.response_field.bind("<<Selection>>", self.update_context_menu)

        # Поле ввода запроса
        self.input_field = tk.Entry(self.root, font=("Arial", 14))
        self.input_field.pack(padx=10, pady=5, fill="x")
        self.input_field.bind("<Return>", self.send_query)  # Обработка нажатия Enter
        self.input_field.focus_set()        # Устанавливаем фокус на поле ввода

        # Кнопка отправки
        self.send_button = tk.Button(self.root, text="Отправить", command=self.send_query)
        self.send_button.pack(pady=5)

        # Радиокнопки выбора режима
        self.radio_frame = tk.Frame(self.root)
        self.radio_frame.pack(pady=5)

        tk.Radiobutton(
            self.radio_frame,
            text="Чатик",
            variable=self.mode,
            value="chat",
            command=self.update_mode_state
        ).pack(side="left")

        tk.Radiobutton(
            self.radio_frame,
            text="Амнезия",
            variable=self.mode,
            value="no_memory",
            command=self.update_mode_state
        ).pack(side="left")


        # Флажок включения chain-of-thought reasoning
        self.cot_mode = tk.BooleanVar(value=False)
        self.cot_checkbox = tk.Checkbutton(
            self.root, text="Умное обоснование (CoT)", variable=self.cot_mode
        )
        self.cot_checkbox.pack(pady=2)

    def update_mode_state(self):
        if self.mode.get() == "chat":
            self.cot_checkbox.config(state="normal")
        else:
            self.cot_checkbox.config(state="disabled")
            self.cot_mode.set(False)

    def send_query(self, event=None):
        """
        Обработчик отправки запроса.
        """
        query = self.input_field.get().strip()
        if not query:
            messagebox.showwarning("Пустой ввод", "Введите запрос!")
            return

        # Очистка поля ввода
        self.input_field.delete(0, tk.END)

        try:
            # Вызов API с учетом выбранного режима работы
            response, self.chat_session = chat_module.generate_response(
                query=query,
                mode=self.mode.get(),  # Передаем текущий режим работы (chat, no_memory)
                chat_session=self.chat_session,  # Передаем текущую сессию чата (если есть)
                cot_mode = self.cot_mode.get()  # Флаг включения Chain-of-Thought
            )

            # Теги цвета должны создаваться ДО вызова insert()
            self.response_field.tag_configure("query", foreground="purple")  # Цвет для запроса
            self.response_field.tag_configure("response", foreground="blue")  # Цвет для ответа

            # Отображение ответа в верхнем поле
            self.response_field.config(state="normal")
            self.response_field.insert("end", f"Запрос: {query}\n\n", "query")
            self.response_field.insert("end", f"Ответ: {response}\n\n", "response")
            self.response_field.config(state="disabled")
            self.response_field.see("end")  # Автопрокрутка к последнему ответу

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

    def show_context_menu(self, event):
        """
        Показать контекстное меню при нажатии правой кнопкой мыши.
        """
        self.update_context_menu()  # Обновляем состояние пунктов меню перед показом
        self.context_menu.post(event.x_root, event.y_root)

    def update_context_menu(self, event=None):
        """
        Обновить состояние пунктов контекстного меню в зависимости от наличия выделения.
        """
        try:
            # Проверяем наличие выделенного текста
            self.response_field.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.context_menu.entryconfig("Копировать", state="normal")
            self.context_menu.entryconfig("Цитировать", state="normal")
        except tk.TclError:
            # Если выделенного текста нет, отключаем пункты
            self.context_menu.entryconfig("Копировать", state="disabled")
            self.context_menu.entryconfig("Цитировать", state="disabled")

    def copy_text(self):
        """
        Копировать выделенный текст из поля вывода.
        """
        selected_text = self.response_field.get(tk.SEL_FIRST, tk.SEL_LAST)
        self.root.clipboard_clear()
        self.root.clipboard_append(selected_text)
        self.root.update()  # Обновить буфер обмена

    def quote_text(self):
        """
        Цитировать выделенный текст в поле ввода.
        """
        try:
            selected_text = self.response_field.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.input_field.insert(tk.END, f'"{selected_text}" ')
            self.input_field.focus_set()  # Устанавливаем фокус на поле ввода

        except tk.TclError:
            messagebox.showwarning("Ошибка", "Не выделен текст для цитирования!")

    def clear_chat(self):
        """
        Очистка текущего чата.
        """
        if messagebox.askyesno("Очистить текущий чат", "Вы уверены?"):
            self.chat_session = None  # Сбрасываем текущую сессию
            self.response_field.config(state="normal")
            self.response_field.delete("1.0", tk.END)  # Очищаем поле вывода
            self.response_field.config(state="disabled")
            messagebox.showinfo("Чат очищен", "Текущая сессия чата была сброшена.")

    def show_tuned_models(self):
        try:
            from google.generativeai import list_tuned_models
            models = list_tuned_models()
            if not models:
                messagebox.showinfo("Мои модели", "У тебя пока нет тюнингованных моделей.")
                return

            info = "\n\n".join(
                f"Название: {m.name}\nОписание: {m.description or '(без описания)'}\nСоздана: {m.create_time}"
                for m in models
            )

            messagebox.showinfo("Мои модели", info)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить список моделей: {e}")

    def train_model_from_dataset(self):
        """
        Вызывает процедуру обучения модели через модуль GeminiChat.
        """
        import GeminiChat  # Импорт здесь, чтобы избежать циклических зависимостей
        GeminiChat.train_model_from_selected_dataset(self.root)

    def load_dataset(self):
        selected_blocks = load_dataset_and_select(self.root)
        if selected_blocks:
            GeminiChat.train_model_from_blocks(selected_blocks)

    def show_progress_window(parent, total_steps):
        progress_win = tk.Toplevel(parent)
        progress_win.title("Обучение модели")
        progress_win.geometry("300x100")
        progress_win.grab_set()

        label = tk.Label(progress_win, text="Идёт обучение модели...")
        label.pack(pady=10)

        pb = ttk.Progressbar(progress_win, maximum=total_steps, length=250, mode="determinate")
        pb.pack(pady=5)
        pb["value"] = 0

        return progress_win, pb

    def select_assistant(self):
        """
        Заглушка для выбора ассистента.
        """
        messagebox.showinfo("Ассистенты", "Функция выбора ассистента пока не реализована.")

    def run(self):
        """
        Запуск интерфейса.
        """
        self.root.mainloop()
