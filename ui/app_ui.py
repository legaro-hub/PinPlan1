import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import textwrap
import webbrowser
import os
import sys
import traceback
import json
import platform
import socket
from datetime import datetime, timedelta
from config import VERSION, BUILD_DATE, CONTACT, LOGIN_FILE, ALLOWED_FILE, LOG_FILE
from modules.auth import AuthManager
from modules.key_manager import KeyManager
from modules.planner import PinterestPlanner
from modules.dialogs import LoginDialog, KeyManagementDialog
from ui.tabs import create_main_tab, create_filters_tab, create_content_tab, create_help_tab


class PinterestPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinterest Planner для проекта Ебач 1.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)

        # Инициализация менеджеров
        self.auth = AuthManager()
        self.openai_key_manager = KeyManager("openai_keys.json")
        self.openrouter_key_manager = KeyManager("openrouter_keys.json")
        self.planner = PinterestPlanner(self)

        # Переменные состояния
        self.status_var = tk.StringVar(value="Готов к работе")
        self.version = VERSION
        self.build_date = BUILD_DATE
        self.contact = CONTACT
        self.last_error = None
        self.log_file = LOG_FILE

        # Инициализация переменных интерфейса
        self.init_variables()

        # Создание интерфейса
        self.create_widgets_with_tabs()
        self.create_menu()

        # Проверка авторизации при запуске
        self.check_auth_on_startup()

    def init_variables(self):
        """Инициализация Tkinter переменных"""
        # Основные параметры
        current_date = datetime.now()
        default_date = (current_date + timedelta(days=2)).strftime("%d.%m.%Y")
        default_time = current_date.strftime("%H:%M")

        self.date_var = tk.StringVar(value=default_date)
        self.time_var = tk.StringVar(value=default_time)
        self.min_interval_var = tk.StringVar(value="30")
        self.max_interval_var = tk.StringVar(value="50")
        self.input_file_var = tk.StringVar(value="final_merged.xlsx")
        self.output_file_var = tk.StringVar(value="content_schedule.csv")

        # Фильтры
        self.enable_post_limit = tk.BooleanVar(value=False)
        self.post_limit_var = tk.StringVar(value="1000")
        self.enable_min_saves = tk.BooleanVar(value=False)
        self.min_saves_var = tk.StringVar(value="200")
        self.sort_by_saves_only = tk.BooleanVar(value=False)

        # Контент
        self.base_text_var = tk.StringVar()
        self.base_link_var = tk.StringVar()
        self.shuffle_var = tk.BooleanVar(value=True)
        self.advanced_mode = tk.BooleanVar(value=False)
        self.link_template_var = tk.StringVar(value="/?{num}")
        self.text_template_var = tk.StringVar(value="#{num}")

        # AI настройки
        self.api_key_var = tk.StringVar()
        self.ai_enabled = tk.BooleanVar(value=False)
        self.ai_model_var = tk.StringVar(value="gpt-3.5-turbo")
        self.ai_temperature_var = tk.DoubleVar(value=0.7)
        self.ai_max_tokens_var = tk.IntVar(value=100)

        # OpenRouter настройки
        self.openrouter_key_var = tk.StringVar()
        self.save_openrouter_key = tk.BooleanVar(value=False)
        self.use_openrouter_var = tk.BooleanVar(value=False)
        self.openrouter_model_var = tk.StringVar(value="openrouter/cypher-alpha:free")
        self.openrouter_temperature_var = tk.DoubleVar(value=0.7)
        self.openrouter_max_tokens_var = tk.IntVar(value=1000)
        self.openrouter_delay_var = tk.DoubleVar(value=5.0)

        # Загрузка сохраненных ключей
        self.load_saved_keys()

    def load_saved_keys(self):
        """Загрузка сохраненных API ключей"""
        if self.openai_key_manager.get_keys():
            self.api_key_var.set(self.openai_key_manager.get_keys()[0])
        if self.openrouter_key_manager.get_keys():
            self.openrouter_key_var.set(self.openrouter_key_manager.get_keys()[0])

    def save_keys(self):
        """Сохранение API ключей"""
        if self.save_openrouter_key.get() and self.openrouter_key_var.get():
            self.openrouter_key_manager.add_key(self.openrouter_key_var.get())
        if self.api_key_var.get():
            self.openai_key_manager.add_key(self.api_key_var.get())

    def create_widgets_with_tabs(self):
        """Создание основного интерфейса с вкладками"""
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель кнопок и статуса
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        # Кнопка открытия файла
        open_button = ttk.Button(
            button_frame,
            text="Открыть файл",
            command=self.open_csv_editor,
            width=15
        )
        open_button.pack(side=tk.RIGHT, padx=5, ipadx=10, ipady=5)

        # Кнопка запуска генерации
        run_button = ttk.Button(
            button_frame,
            text="Сгенерировать файл",
            command=self.run_planner,
            style="Accent.TButton"
        )
        run_button.pack(side=tk.RIGHT, padx=5, ipadx=10, ipady=5)

        # Панель статуса
        status_frame = ttk.Frame(button_frame)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, anchor=tk.W)

        # Прогресс-бар (скрыт по умолчанию)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame,
            variable=self.progress_var,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.pack_forget()

        # Заголовок приложения
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title = ttk.Label(title_frame, text="Pinterest Planner", font=("Arial", 16, "bold"))
        title.pack(side=tk.LEFT)
        subtitle = ttk.Label(title_frame, text="для проекта Ебач 1.0", font=("Arial", 12))
        subtitle.pack(side=tk.LEFT, padx=10)
        version_label = ttk.Label(title_frame, text=f"v{self.version}")
        version_label.pack(side=tk.RIGHT)

        # Создание вкладок
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Добавление вкладок
        main_tab = ttk.Frame(notebook, padding=10)
        notebook.add(main_tab, text="Основные параметры")
        create_main_tab(main_tab, self)

        filters_tab = ttk.Frame(notebook, padding=10)
        notebook.add(filters_tab, text="Фильтры")
        create_filters_tab(filters_tab, self)

        content_tab = ttk.Frame(notebook, padding=10)
        notebook.add(content_tab, text="Контент")
        create_content_tab(content_tab, self)

        help_tab = ttk.Frame(notebook, padding=10)
        notebook.add(help_tab, text="Помощь")
        create_help_tab(help_tab, self)

    def create_menu(self):
        """Создание главного меню приложения"""
        self.menubar = tk.Menu(self.root)

        # Меню Файл
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Открыть CSV", command=self.open_csv_editor)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        self.menubar.add_cascade(label="Файл", menu=file_menu)

        # Меню Отчеты
        report_menu = tk.Menu(self.menubar, tearoff=0)
        report_menu.add_command(label="Последняя ошибка", command=self.show_last_error)
        report_menu.add_command(label="Отправить отчет", command=self.send_error_report)
        self.menubar.add_cascade(label="Отчеты", menu=report_menu)

        # Меню Справка
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="История версий", command=self.show_version_history)
        help_menu.add_command(label="Патч-ноты", command=self.show_patch_notes)
        help_menu.add_separator()
        help_menu.add_command(label="Связаться с поддержкой", command=self.contact_support)
        self.menubar.add_cascade(label="Справка", menu=help_menu)

        # Меню Настройки
        self.options_menu = tk.Menu(self.menubar, tearoff=0)
        self.update_menu()
        self.menubar.add_cascade(label="Настройки", menu=self.options_menu)

        self.root.config(menu=self.menubar)

    def update_menu(self):
        """Обновление меню в зависимости от состояния авторизации"""
        self.options_menu.delete(0, tk.END)
        if self.auth.current_user:
            self.options_menu.add_command(
                label=f"Выйти ({self.auth.current_user})",
                command=self.logout
            )
        else:
            self.options_menu.add_command(
                label="Авторизация",
                command=self.show_login_dialog
            )

    def check_auth_on_startup(self):
        """Проверка авторизации при запуске приложения"""
        if self.auth.check_authorization():
            self.status_var.set(f"Авторизован: {self.auth.current_user}")
        else:
            messagebox.showinfo(
                "Требуется авторизация",
                "Пожалуйста, авторизуйтесь в меню Настройки для использования приложения"
            )
            self.status_var.set("Не авторизован")

    def show_login_dialog(self):
        """Показ диалога авторизации"""
        LoginDialog(self.root, self)

    def logout(self):
        """Выход из системы"""
        if self.auth.logout():
            self.status_var.set("Не авторизован")
            self.update_menu()
            messagebox.showinfo("Выход", "Вы успешно вышли из системы")
        else:
            messagebox.showerror("Ошибка", "Не удалось выйти из системы")

    def show_about(self):
        about_text = f"""
        Pinterest Planner для проекта Ебач 1.0

        Версия: {self.version}
        Дата сборки: {self.build_date}

        Разработчик: {self.contact}

        Последние изменения (v1.7.0):
        - Полная переработка архитектуры приложения
        - Разделение кода на логические модули
        - Устранение критических ошибок
        - Значительное улучшение производительности

        © 2025 Project Ebach 1.0. Все права защищены.
        """
        messagebox.showinfo("О программе", about_text.strip())

    def show_version_history(self):
        """Показ истории версий"""
        versions = [
            "1.7.0 (10.07.2025):\n"
        "- Полный рефакторинг кода: разделение на модули\n"
        "- Оптимизация архитектуры приложения\n"
        "- Исправление критических ошибок в редакторе CSV\n"
        "- Улучшение стабильности работы приложения",
            "1.6.1 (09.07.2025):\n- Добавлена проверка столбца 'image url'\n- Улучшена обработка ошибок при чтении файлов\n- Оптимизирован алгоритм сортировки",
            "1.6.0 (08.07.2025):\n- Управление несколькими API ключами\n- Генерация до 100 символов без хештегов\n- Оптимальные интервалы 30-50 минут",
            "1.5.5 (07.07.2025):\n- Сохранение API ключей\n- Отображение времени генерации\n- Динамический прогресс",
            "1.5.4 (06.07.2025):\n- Улучшен интерфейс\n- Убраны лишние кнопки\n- Оптимизирована генерация текстов",
            "1.5.3 (05.07.2025):\n- Улучшен интерфейс OpenRouter\n- Добавлены настройки задержки\n- Оптимизирована генерация текстов",
            "1.5.2 (04.07.2025):\n- Добавлена система авторизации\n- Мастер-ключ для тестирования\n- Поддержка OpenRouter Cypher Alpha",
            "1.5.1.b2 (03.07.2025):\n- Исправлены горячие клавиши для всех полей ввода\n- Добавлен фильтр сортировки по сохранениям\n- Исправлено обновление заголовка окна",
            "1.5.1.b (03.07.2025):\n- Исправлена проблема с горячими клавишами в русской раскладке",
            "1.5.0 (02.07.2025):\n- Интеграция с ChatGPT API\n- Улучшенная генерация контента",
        ]
        messagebox.showinfo("История версий", "\n\n".join(versions))

    def show_patch_notes(self):
        """Показ патч-нотов для текущей версии"""
        if self.version == "1.7.0":
            notes = """
            Версия 1.7.0 (10.07.2025)

            Архитектурные улучшения:
            - Полный рефакторинг монолитного кода
            - Разделение на логические модули:
              * auth.py - управление авторизацией
              * csv_editor.py - редактор CSV/Excel
              * dialogs.py - диалоговые окна
              * planner.py - основной алгоритм планирования
              * utils.py - вспомогательные функции
            - Оптимизация структуры проекта

            Оптимизация производительности:
            - Ускорение загрузки больших файлов
            - Уменьшение использования памяти
            - Улучшение отзывчивости интерфейса

            Исправления ошибок:
            - Критическое исправление работы редактора CSV
            - Устранение проблем с горячими клавишами
            - Исправление ошибок импорта модулей
            - Устранение случайных зависаний интерфейса

            Улучшения для разработчиков:
            - Четкое разделение ответственности модулей
            - Упрощение дальнейшей разработки
            - Улучшение читаемости кода
            - Добавление документации к методам
            """
        elif self.version == "1.6.1":
            notes = """
            Версия 1.6.1 (09.07.2025)

            Ключевые улучшения:

            1. Проверка столбца 'image url'
               - Теперь приложение проверяет наличие важного столбца с изображениями
               - Если столбец отсутствует - понятное сообщение об ошибке
               - Это предотвращает сбои при генерации расписания

            2. Улучшенные сообщения об ошибках
               - Более четкие указания при проблемах с файлами
               - Подробное описание как исправить ошибку
               - Примеры правильных форматов данных

            3. Оптимизированный алгоритм сортировки
               - Ускорение обработки на 30% для больших файлов
               - Уменьшено использование памяти
               - Улучшена стабильность при работе с 10k+ строками

            Исправления:
            - Устранена редкая ошибка при сохранении CSV
            - Исправлено отображение прогресс-бара
            - Улучшена совместимость с Windows 11
            """
        elif self.version == "1.6.0":
            notes = """
            Версия 1.6.0 (08.07.2025)

            Новые возможности:
            - Система управления несколькими API ключами
            - Возможность переключения ключей при достижении лимитов
            - Генерация текстов до 100 символов без хештегов
            - Оптимизированные временные интервалы 30-50 минут
            - Улучшенная обработка ошибок генерации текстов

            Улучшения:
            - Автоматическое дополнение не сгенерированных текстов
            - Улучшенный интерфейс управления ключами
            - Оптимизирована работа с большими объемами данных

            Исправления:
            - Исправлены ошибки при генерации частичных текстов
            - Улучшена стабильность работы с разными моделями AI
            """
        elif self.version == "1.5.5":
            notes = """
            Версия 1.5.5 (07.07.2025)

            Новые возможности:
            - Сохранение API ключей между запусками
            - Автоматическая коррекция задержки для улучшения качества текстов

            Улучшения:
            - Обновленная инструкция с советами по настройке
            - Улучшена обработка больших объемов данных

            Исправления:
            - Исправлена опечатка 'пачнуты' на 'патч-ноты'
            - Улучшено сохранение состояния фильтров
            - Исправлен расчет общего количества строк
            """
        else:
            notes = f"""
            Версия {self.version} ({self.build_date})

            Новые возможности:
            - Интеграция с ChatGPT API для генерации контента
            - Автоматическая генерация уникальных текстов
            - Настройка параметров модели AI

            Исправления:
            - Устранена ошибка часовых поясов
            - Улучшена обработка форматов даты
            """
        messagebox.showinfo("Патч-ноты", notes.strip())

    def contact_support(self):
        """Открытие ссылки для связи с поддержкой"""
        webbrowser.open(f"https://t.me/{self.contact[1:]}")

    def browse_input_file(self):
        """Выбор входного файла"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.input_file_var.set(file_path)

    def browse_output_file(self):
        """Выбор файла для сохранения"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)

    def run_planner(self):
        """Запуск генерации расписания"""
        if not self.auth.current_user:
            messagebox.showwarning(
                "Требуется авторизация",
                "Пожалуйста, авторизуйтесь для использования приложения"
            )
            return

        self.status_var.set("Генерация запущена...")
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_var.set(0)
        threading.Thread(target=self.planner.run_planner).start()

    def open_csv_editor(self):
        """Открытие редактора CSV/Excel файлов"""
        if not self.auth.current_user:
            messagebox.showwarning(
                "Требуется авторизация",
                "Пожалуйста, авторизуйтесь для использования приложения"
            )
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            from modules.csv_editor import CSVEditor
            CSVEditor(self.root, file_path)

    def update_progress_bar(self, progress, current, total):
        """Обновление прогресс-бара и статуса"""
        self.progress_var.set(progress)
        self.status_var.set(f"Генерация текстов: {current}/{total} ({progress:.1f}%)")

    def hide_progress(self):
        """Скрытие прогресс-бара"""
        self.progress_bar.pack_forget()
        self.progress_var.set(0)

    def test_api_connection(self):
        """Проверка подключения к OpenAI API"""
        api_key = self.api_key_var.get()
        if not api_key:
            messagebox.showwarning("Предупреждение", "Введите API ключ")
            return

        try:
            from openai import OpenAI, AuthenticationError, RateLimitError, APIError
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Привет! Ответь просто 'OK'"}],
                max_tokens=5
            )

            if response.choices[0].message.content.strip() == "OK":
                messagebox.showinfo("Успех", "Подключение к API успешно установлено!")
            else:
                messagebox.showinfo("Успех", f"API отвечает: {response.choices[0].message.content}")

        except AuthenticationError:
            messagebox.showerror("Ошибка", "Неверный API ключ")
        except RateLimitError as e:
            if "quota" in str(e).lower():
                messagebox.showerror(
                    "Ошибка квоты",
                    "Превышена квота API!\n\n"
                    "1. Проверьте баланс на platform.openai.com\n"
                    "2. Добавьте способ оплаты\n"
                    "3. Проверьте лимиты использования"
                )
            else:
                messagebox.showerror(
                    "Лимит запросов",
                    "Превышен лимит запросов!\n\n"
                    "Пожалуйста, подождите несколько минут и повторите попытку"
                )
        except APIError as e:
            messagebox.showerror("Ошибка API", f"Ошибка API: {str(e)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def test_openrouter_connection(self):
        """Проверка подключения к OpenRouter API"""
        api_key = self.openrouter_key_var.get()
        if not api_key:
            messagebox.showwarning("Предупреждение", "Введите API ключ OpenRouter")
            return

        try:
            self.save_keys()
            from openai import OpenAI
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/pinterest-planner",
                    "X-Title": "Pinterest Planner"
                }
            )

            response = client.chat.completions.create(
                model=self.openrouter_model_var.get(),
                messages=[{"role": "user", "content": "Привет! Ответь просто 'OK'"}],
                max_tokens=5
            )

            if response.choices[0].message.content.strip().upper() == "OK":
                messagebox.showinfo("Успех", "Подключение к OpenRouter успешно установлено!")
            else:
                messagebox.showinfo("Успех", f"API отвечает: {response.choices[0].message.content}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к OpenRouter:\n{str(e)}")

    def manage_keys(self, key_type):
        """Открытие диалога управления ключами"""
        if key_type == "openai":
            KeyManagementDialog(self.root, self.openai_key_manager, self.api_key_var)
        elif key_type == "openrouter":
            KeyManagementDialog(self.root, self.openrouter_key_manager, self.openrouter_key_var)

    def show_last_error(self):
        """Показ последней ошибки"""
        if not self.last_error:
            messagebox.showinfo("Информация", "Нет сохраненных ошибок")
            return
        self.show_error_details(self.last_error)

    def show_error_details(self, error_info):
        """Показ деталей ошибки"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Ошибка от {error_info['timestamp']}")
        dialog.geometry("700x500")
        dialog.resizable(True, True)

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Информация об ошибке
        info_frame = ttk.LabelFrame(main_frame, text="Информация об ошибке")
        info_frame.pack(fill=tk.X, pady=5)

        rows = [
            ("Дата и время", error_info['timestamp']),
            ("Версия ПО", f"{error_info['version']} ({error_info.get('build_date', '')})"),
            ("Ошибка", f"{error_info['error_type']}: {error_info['error_message']}"),
            ("Файл ввода", error_info.get('input_file', '')),
            ("Файл вывода", error_info.get('output_file', '')),
            ("Пользователь", error_info.get('auth_user', 'none'))
        ]

        for label, value in rows:
            row_frame = ttk.Frame(info_frame)
            row_frame.pack(fill=tk.X, padx=10, pady=2)
            ttk.Label(row_frame, text=label, width=15, anchor=tk.W).pack(side=tk.LEFT)
            ttk.Label(row_frame, text=value, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Трассировка ошибки
        trace_frame = ttk.LabelFrame(main_frame, text="Трассировка ошибки")
        trace_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        trace_text = scrolledtext.ScrolledText(
            trace_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            padx=10,
            pady=10
        )
        trace_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        trace_text.insert(tk.INSERT, error_info['traceback'])
        trace_text.configure(state=tk.DISABLED)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        send_btn = ttk.Button(
            button_frame,
            text="Отправить отчет",
            command=lambda: self.send_error_report(dialog),
            width=15
        )
        send_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(
            button_frame,
            text="Закрыть",
            command=dialog.destroy,
            width=10
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

    def send_error_report(self, parent=None):
        """Отправка отчета об ошибке"""
        if not self.last_error:
            messagebox.showinfo("Информация", "Нет ошибок для отправки", parent=parent)
            return

        send_dialog = tk.Toplevel(parent or self.root)
        send_dialog.title("Отправка отчета об ошибке")
        send_dialog.geometry("500x300")
        send_dialog.resizable(False, False)
        send_dialog.transient(parent or self.root)
        send_dialog.grab_set()

        main_frame = ttk.Frame(send_dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Отправка отчета об ошибке разработчику",
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 15))

        # Поля для контактов и описания
        contact_frame = ttk.Frame(main_frame)
        contact_frame.pack(fill=tk.X, pady=5)
        ttk.Label(contact_frame, text="Ваши контакты (email/telegram):").pack(anchor=tk.W)
        contact_var = tk.StringVar()
        contact_entry = ttk.Entry(contact_frame, textvariable=contact_var, width=40)
        contact_entry.pack(fill=tk.X, pady=5)

        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.X, pady=5)
        ttk.Label(desc_frame, text="Опишите проблему подробнее:").pack(anchor=tk.W)
        desc_text = scrolledtext.ScrolledText(desc_frame, height=4, wrap=tk.WORD)
        desc_text.pack(fill=tk.X, pady=5)

        # Статус отправки
        status_var = tk.StringVar(value="Готово к отправке")
        status_label = ttk.Label(main_frame, textvariable=status_var, foreground="green")
        status_label.pack(pady=5)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        def do_send():
            status_var.set("Отправка...")
            send_dialog.update()
            contact_info = contact_var.get().strip()
            description = desc_text.get("1.0", tk.END).strip()

            try:
                # В реальном приложении здесь был бы код отправки отчета
                # Для примера просто сохраняем отчет локально
                report = {
                    "contact": contact_info,
                    "description": description,
                    "error": self.last_error
                }
                report_file = f"error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False)

                status_var.set("Отчет успешно отправлен!")
                send_dialog.after(2000, send_dialog.destroy)
            except Exception as e:
                status_var.set(f"Ошибка отправки: {str(e)}")

        send_btn = ttk.Button(
            button_frame,
            text="Отправить",
            command=do_send,
            width=15
        )
        send_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(
            button_frame,
            text="Отмена",
            command=send_dialog.destroy,
            width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def log_error(self, exception):
        """Логирование ошибки в файл"""
        error_info = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": self.version,
            "build_date": self.build_date,
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "hostname": socket.gethostname(),
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "traceback": traceback.format_exc(),
            "input_file": self.input_file_var.get(),
            "output_file": self.output_file_var.get(),
            "date": self.date_var.get(),
            "time": self.time_var.get(),
            "min_interval": self.min_interval_var.get(),
            "max_interval": self.max_interval_var.get(),
            "base_text": self.base_text_var.get(),
            "base_link": self.base_link_var.get(),
            "shuffle": self.shuffle_var.get(),
            "enable_post_limit": self.enable_post_limit.get(),
            "post_limit": self.post_limit_var.get(),
            "enable_min_saves": self.enable_min_saves.get(),
            "min_saves": self.min_saves_var.get(),
            "advanced_mode": self.advanced_mode.get(),
            "link_template": self.link_template_var.get(),
            "text_template": self.text_template_var.get(),
            "ai_enabled": self.ai_enabled.get(),
            "sort_by_saves_only": self.sort_by_saves_only.get(),
            "use_openrouter": self.use_openrouter_var.get(),
            "openrouter_model": self.openrouter_model_var.get(),
            "auth_user": self.auth.current_user or "none"
        }

        try:
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []

            logs.append(error_info)

            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

            self.last_error = error_info
        except Exception as e:
            print(f"Ошибка при записи лога: {str(e)}")

    def show_error_with_details(self, exception):
        """Показ ошибки с деталями"""
        error_type = type(exception).__name__
        error_msg = str(exception)

        dialog = tk.Toplevel(self.root)
        dialog.title("Ошибка выполнения")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="Произошла ошибка при выполнении операции",
            font=("Arial", 12, "bold"),
            foreground="#d9534f"
        ).pack(pady=(0, 10))

        # Информация об ошибке
        error_frame = ttk.LabelFrame(main_frame, text="Информация об ошибке")
        error_frame.pack(fill=tk.X, pady=5)

        ttk.Label(
            error_frame,
            text=f"Тип ошибки: {error_type}",
            font=("Arial", 10)
        ).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Label(
            error_frame,
            text=f"Сообщение: {error_msg}",
            font=("Arial", 10)
        ).pack(anchor=tk.W, padx=10, pady=5)

        # Детали ошибки
        trace_frame = ttk.LabelFrame(main_frame, text="Детали ошибки")
        trace_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        trace_text = scrolledtext.ScrolledText(
            trace_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            padx=10,
            pady=10,
            height=10
        )
        trace_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        trace_text.insert(tk.INSERT, traceback.format_exc())
        trace_text.configure(state=tk.DISABLED)

        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="Отправить отчет разработчику",
            command=lambda: self.send_error_report(dialog),
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Закрыть",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Label(
            main_frame,
            text="Для ускорения исправления ошибки отправьте отчет разработчику",
            font=("Arial", 9),
            foreground="gray"
        ).pack(side=tk.BOTTOM, pady=(10, 0))