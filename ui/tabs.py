import tkinter as tk
from tkinter import ttk, scrolledtext
import textwrap
from modules.utils import bind_paste_shortcut, format_date_input, format_time_input, toggle_advanced_settings, toggle_openrouter_settings, toggle_ai_settings, toggle_entry_state, correct_delay_value, update_openai_keys, update_openrouter_keys

def create_main_tab(parent, app):
    """Создает вкладку 'Основные параметры'"""
    source_frame = ttk.LabelFrame(parent, text="Источник данных")
    source_frame.pack(fill=tk.X, pady=5, padx=5)

    # Поле для файла Excel
    file_row = ttk.Frame(source_frame)
    file_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(file_row, text="Файл Excel:").pack(side=tk.LEFT, padx=(0, 5))
    file_entry = ttk.Entry(file_row, textvariable=app.input_file_var, width=70)
    file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    bind_paste_shortcut(file_entry)
    ttk.Button(file_row, text="Обзор", command=app.browse_input_file, width=10).pack(side=tk.LEFT)

    # Поле для файла сохранения
    save_row = ttk.Frame(source_frame)
    save_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(save_row, text="Файл для сохранения:").pack(side=tk.LEFT, padx=(0, 5))
    save_entry = ttk.Entry(save_row, textvariable=app.output_file_var, width=70)
    save_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    bind_paste_shortcut(save_entry)
    ttk.Button(save_row, text="Обзор", command=app.browse_output_file, width=10).pack(side=tk.LEFT)

    # Информация о требуемых колонках
    ttk.Label(
        source_frame,
        text="Файл должен содержать столбцы: image url, created date, saves",
        font=("Arial", 9),
        foreground="gray"
    ).pack(pady=(5, 0), anchor=tk.W, padx=10)

    # Настройки расписания
    schedule_frame = ttk.LabelFrame(parent, text="Расписание")
    schedule_frame.pack(fill=tk.X, pady=5, padx=5)

    # Дата и время начала
    datetime_row = ttk.Frame(schedule_frame)
    datetime_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(datetime_row, text="Дата начала:").pack(side=tk.LEFT, padx=(0, 5))
    date_entry = ttk.Entry(datetime_row, textvariable=app.date_var, width=15)
    date_entry.pack(side=tk.LEFT, padx=(0, 15))
    date_entry.bind("<KeyRelease>", lambda e: format_date_input(e, app.date_var))
    bind_paste_shortcut(date_entry)

    ttk.Label(datetime_row, text="Время начала:").pack(side=tk.LEFT, padx=(0, 5))
    time_entry = ttk.Entry(datetime_row, textvariable=app.time_var, width=10)
    time_entry.pack(side=tk.LEFT)
    time_entry.bind("<KeyRelease>", lambda e: format_time_input(e, app.time_var))
    bind_paste_shortcut(time_entry)

    # Интервалы между постами
    interval_row = ttk.Frame(schedule_frame)
    interval_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(interval_row, text="Мин. интервал (мин):").pack(side=tk.LEFT, padx=(0, 5))
    min_entry = ttk.Entry(interval_row, textvariable=app.min_interval_var, width=10)
    min_entry.pack(side=tk.LEFT, padx=(0, 15))
    bind_paste_shortcut(min_entry)

    ttk.Label(interval_row, text="Макс. интервал (мин):").pack(side=tk.LEFT, padx=(0, 5))
    max_entry = ttk.Entry(interval_row, textvariable=app.max_interval_var, width=10)
    max_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(max_entry)

def create_filters_tab(parent, app):
    """Создает вкладку 'Фильтры'"""
    filters_frame = ttk.LabelFrame(parent, text="Фильтры контента")
    filters_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

    # Ограничение количества постов
    post_limit_frame = ttk.Frame(filters_frame)
    post_limit_frame.pack(fill=tk.X, pady=10, padx=10)
    post_limit_cb = ttk.Checkbutton(
        post_limit_frame,
        text="Ограничить количество постов:",
        variable=app.enable_post_limit,
        command=lambda: toggle_entry_state(post_limit_entry, app.enable_post_limit)
    )
    post_limit_cb.pack(side=tk.LEFT, padx=(0, 10))
    post_limit_entry = ttk.Entry(post_limit_frame, textvariable=app.post_limit_var, width=10, state=tk.DISABLED)
    post_limit_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(post_limit_entry)
    toggle_entry_state(post_limit_entry, app.enable_post_limit)

    # Минимальное количество сохранений
    min_saves_frame = ttk.Frame(filters_frame)
    min_saves_frame.pack(fill=tk.X, pady=10, padx=10)
    min_saves_cb = ttk.Checkbutton(
        min_saves_frame,
        text="Минимальное количество сохранений:",
        variable=app.enable_min_saves,
        command=lambda: toggle_entry_state(min_saves_entry, app.enable_min_saves)
    )
    min_saves_cb.pack(side=tk.LEFT, padx=(0, 10))
    min_saves_entry = ttk.Entry(min_saves_frame, textvariable=app.min_saves_var, width=10, state=tk.DISABLED)
    min_saves_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(min_saves_entry)
    toggle_entry_state(min_saves_entry, app.enable_min_saves)

    # Сортировка только по сохранениям
    sort_frame = ttk.Frame(filters_frame)
    sort_frame.pack(fill=tk.X, pady=10, padx=10)
    sort_cb = ttk.Checkbutton(
        sort_frame,
        text="Сортировать только по количеству сохранений (без веса)",
        variable=app.sort_by_saves_only
    )
    sort_cb.pack(anchor=tk.W)

def create_content_tab(parent, app):
    """Создает вкладку 'Контент'"""
    content_frame = ttk.LabelFrame(parent, text="Настройки контента")
    content_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

    # Базовый текст
    text_row = ttk.Frame(content_frame)
    text_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(text_row, text="Базовый текст (тема для генерации):").pack(side=tk.LEFT, padx=(0, 5), anchor=tk.N)
    text_entry = ttk.Entry(text_row, textvariable=app.base_text_var, width=70)
    text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    bind_paste_shortcut(text_entry)

    # Telegram ссылка
    link_row = ttk.Frame(content_frame)
    link_row.pack(fill=tk.X, pady=5, padx=5)
    ttk.Label(link_row, text="Telegram ссылка:").pack(side=tk.LEFT, padx=(0, 5), anchor=tk.N)
    link_entry = ttk.Entry(link_row, textvariable=app.base_link_var, width=70)
    link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    bind_paste_shortcut(link_entry)

    # Перемешивание постов
    shuffle_row = ttk.Frame(content_frame)
    shuffle_row.pack(fill=tk.X, pady=5, padx=5)
    shuffle_cb = ttk.Checkbutton(
        shuffle_row,
        text="Перемешать строки после создания расписания",
        variable=app.shuffle_var
    )
    shuffle_cb.pack(anchor=tk.W)

    # Расширенные настройки
    advanced_frame = ttk.LabelFrame(content_frame, text="Расширенные настройки")
    advanced_frame.pack(fill=tk.X, pady=10, padx=5)
    advanced_cb = ttk.Checkbutton(
        advanced_frame,
        text="Использовать расширенные настройки",
        variable=app.advanced_mode,
        command=lambda: toggle_advanced_settings(advanced_settings_frame, app.advanced_mode)
    )
    advanced_cb.pack(anchor=tk.W, pady=(0, 5))
    advanced_settings_frame = ttk.Frame(advanced_frame)
    toggle_advanced_settings(advanced_settings_frame, app.advanced_mode)

    # Шаблон ссылки
    link_template_row = ttk.Frame(advanced_settings_frame)
    link_template_row.pack(fill=tk.X, pady=2)
    ttk.Label(link_template_row, text="Шаблон ссылки:").pack(side=tk.LEFT, padx=(0, 5))
    link_template_entry = ttk.Entry(link_template_row, textvariable=app.link_template_var, width=30)
    link_template_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(link_template_entry)

    # Шаблон текста
    text_template_row = ttk.Frame(advanced_settings_frame)
    text_template_row.pack(fill=tk.X, pady=2)
    ttk.Label(text_template_row, text="Шаблон текста:").pack(side=tk.LEFT, padx=(0, 5))
    text_template_entry = ttk.Entry(text_template_row, textvariable=app.text_template_var, width=30)
    text_template_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(text_template_entry)

    # Настройки OpenRouter
    openrouter_frame = ttk.LabelFrame(content_frame, text="OpenRouter Cypher Alpha")
    openrouter_frame.pack(fill=tk.X, pady=10, padx=5)
    openrouter_cb = ttk.Checkbutton(
        openrouter_frame,
        text="Использовать OpenRouter (Cypher Alpha)",
        variable=app.use_openrouter_var,
        command=lambda: toggle_openrouter_settings(openrouter_settings_frame, app.use_openrouter_var)
    )
    openrouter_cb.pack(anchor=tk.W, pady=(0, 5))
    openrouter_settings_frame = ttk.Frame(openrouter_frame)
    toggle_openrouter_settings(openrouter_settings_frame, app.use_openrouter_var)

    # Поле для ключа OpenRouter
    key_frame = ttk.Frame(openrouter_settings_frame)
    key_frame.pack(fill=tk.X, pady=5)
    ttk.Label(key_frame, text="API ключ OpenRouter:").pack(side=tk.LEFT, padx=(0, 5))
    openrouter_combo = ttk.Combobox(key_frame, textvariable=app.openrouter_key_var, width=45)
    openrouter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
    update_openrouter_keys(openrouter_combo, app.openrouter_key_manager, app.openrouter_key_var)

    # Кнопки управления ключами
    manage_btn = ttk.Button(
        key_frame,
        text="Управление",
        command=lambda: app.manage_keys("openrouter"),
        width=10
    )
    manage_btn.pack(side=tk.LEFT, padx=5)
    test_btn = ttk.Button(
        key_frame,
        text="Проверить",
        command=app.test_openrouter_connection,
        width=10
    )
    test_btn.pack(side=tk.RIGHT, padx=5)

    # Сохранение ключа
    save_key_frame = ttk.Frame(openrouter_settings_frame)
    save_key_frame.pack(fill=tk.X, pady=5)
    save_key_cb = ttk.Checkbutton(
        save_key_frame,
        text="Сохранить текущий ключ",
        variable=app.save_openrouter_key
    )
    save_key_cb.pack(anchor=tk.W)

    # Дополнительные параметры OpenRouter
    settings_frame = ttk.Frame(openrouter_settings_frame)
    settings_frame.pack(fill=tk.X, padx=5, pady=5)
    model_frame = ttk.Frame(settings_frame)
    model_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(model_frame, text="Модель:").pack(anchor=tk.W)
    model_combo = ttk.Combobox(model_frame, textvariable=app.openrouter_model_var, width=25)
    model_combo['values'] = (
        'openrouter/cypher-alpha:free',
        'openrouter/mistralai/mistral-7b-instruct:free',
        'openrouter/google/palm-2-chat-bison:free'
    )
    model_combo.pack(fill=tk.X)

    # Температура генерации
    temp_frame = ttk.Frame(settings_frame)
    temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(temp_frame, text="Температура:").pack(anchor=tk.W)
    temp_scale = ttk.Scale(temp_frame, from_=0.1, to=1.0, variable=app.openrouter_temperature_var)
    temp_scale.pack(fill=tk.X)
    ttk.Label(temp_frame, textvariable=app.openrouter_temperature_var).pack()

    # Максимальное количество токенов
    tokens_frame = ttk.Frame(settings_frame)
    tokens_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(tokens_frame, text="Макс. токенов:").pack(anchor=tk.W)
    tokens_spin = ttk.Spinbox(tokens_frame, from_=50, to=4000, textvariable=app.openrouter_max_tokens_var, width=10)
    tokens_spin.pack(fill=tk.X)

    # Задержка между запросами
    delay_frame = ttk.Frame(openrouter_settings_frame)
    delay_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(delay_frame, text="Задержка между запросами (сек, мин. 5):").pack(side=tk.LEFT, padx=(0, 5))
    delay_entry = ttk.Entry(delay_frame, textvariable=app.openrouter_delay_var, width=10)
    delay_entry.pack(side=tk.LEFT)
    bind_paste_shortcut(delay_entry)
    delay_entry.bind("<FocusOut>", lambda e: correct_delay_value(app.openrouter_delay_var))

    # Информация о Cypher Alpha
    info_frame = ttk.Frame(openrouter_settings_frame)
    info_frame.pack(fill=tk.X, pady=5)
    ttk.Label(
        info_frame,
        text="Cypher Alpha - бесплатная модель с 1M токенов контекста.\nAPI совместимо с OpenAI, без ограничений.",
        font=("Arial", 9),
        foreground="gray"
    ).pack(anchor=tk.W)

    # Настройки ChatGPT
    ai_frame = ttk.LabelFrame(content_frame, text="Интеграция с ChatGPT")
    ai_frame.pack(fill=tk.X, pady=10, padx=5)
    ai_enable_frame = ttk.Frame(ai_frame)
    ai_enable_frame.pack(fill=tk.X, padx=5, pady=5)
    ai_cb = ttk.Checkbutton(
        ai_enable_frame,
        text="Использовать ChatGPT для генерации текстов",
        variable=app.ai_enabled,
        command=lambda: toggle_ai_settings(ai_settings_frame, app.ai_enabled)
    )
    ai_cb.pack(anchor=tk.W)
    ai_settings_frame = ttk.Frame(ai_frame)
    toggle_ai_settings(ai_settings_frame, app.ai_enabled)

    # Поле для ключа OpenAI
    api_frame = ttk.Frame(ai_settings_frame)
    api_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(api_frame, text="API ключ OpenAI:").pack(side=tk.LEFT, padx=(0, 5))
    api_combo = ttk.Combobox(api_frame, textvariable=app.api_key_var, width=45)
    api_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
    update_openai_keys(api_combo, app.openai_key_manager, app.api_key_var)

    # Кнопки управления ключами
    manage_btn = ttk.Button(
        api_frame,
        text="Управление",
        command=lambda: app.manage_keys("openai"),
        width=10
    )
    manage_btn.pack(side=tk.LEFT, padx=5)
    test_btn = ttk.Button(api_frame, text="Проверить", command=app.test_api_connection, width=10)
    test_btn.pack(side=tk.RIGHT, padx=5)

    # Параметры модели AI
    settings_frame = ttk.Frame(ai_settings_frame)
    settings_frame.pack(fill=tk.X, padx=5, pady=5)
    model_frame = ttk.Frame(settings_frame)
    model_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(model_frame, text="Модель:").pack(anchor=tk.W)
    model_combo = ttk.Combobox(model_frame, textvariable=app.ai_model_var, width=20)
    model_combo['values'] = ('gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo')
    model_combo.pack(fill=tk.X)

    # Температура генерации
    temp_frame = ttk.Frame(settings_frame)
    temp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
    ttk.Label(temp_frame, text="Температура:").pack(anchor=tk.W)
    temp_scale = ttk.Scale(temp_frame, from_=0.1, to=1.0, variable=app.ai_temperature_var)
    temp_scale.pack(fill=tk.X)
    ttk.Label(temp_frame, textvariable=app.ai_temperature_var).pack()

    # Максимальное количество токенов
    tokens_frame = ttk.Frame(settings_frame)
    tokens_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    ttk.Label(tokens_frame, text="Макс. токенов:").pack(anchor=tk.W)
    tokens_spin = ttk.Spinbox(tokens_frame, from_=50, to=1000, textvariable=app.ai_max_tokens_var, width=10)
    tokens_spin.pack(fill=tk.X)

def create_help_tab(parent, app):
    """Создает вкладку 'Помощь'"""
    help_frame = ttk.LabelFrame(parent, text="Инструкция по использованию")
    help_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

    # Текстовая область с инструкцией
    help_text = scrolledtext.ScrolledText(
        help_frame,
        wrap=tk.WORD,
        font=("Arial", 10),
        padx=10,
        pady=10
    )
    help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Форматирование инструкции
    instructions = textwrap.dedent(f"""
    📌 Инструкция по использованию Pinterest Planner v{app.version}

    🔒 Система авторизации:
       - Для использования приложения требуется авторизация
       - Авторизуйтесь в меню Настройки -> Авторизация
       - Используйте email, предоставленный администратором
       - Опция "Сохранить вход" запомнит вас на этом устройстве

    🚀 1. Подготовка данных:
       - Подготовьте Excel-файл со столбцами: 
         * image url (ссылка на изображение)
         * created date (дата создания пина)
         * saves (количество сохранений)
       - Поддерживаются различные форматы дат
       - Сохранения должны быть числовым значением

    ⏱ 2. Генерация расписания:
       - На вкладке "Основные параметры" укажите:
         * Файл с пинами
         * Путь для сохранения CSV
         * Дата и время начала публикаций
         * Интервалы между постами (рекомендуется 30-50 минут)
       - На вкладке "Фильтры" настройте критерии отбора контента
       - На вкладке "Контент" укажите:
         * Базовый текст - тема для генерации заголовков
         * Telegram ссылку
       - Нажмите "Сгенерировать файл"
       - Импортируйте полученный CSV в SMMBox

    🤖 3. Интеграция с AI:
       - OpenRouter Cypher Alpha (бесплатно, 1M токенов контекста):
         * Включите опцию "Использовать OpenRouter"
         * Выберите или добавьте API ключ OpenRouter
         * Настройте параметры генерации: модель, температура, токены
       - ChatGPT (требуется API ключ OpenAI):
         * Выберите или добавьте API ключ OpenAI
         * Настройте параметры модели

    💡 Советы по генерации текстов:
       - Базовый текст используется как тема для генерации заголовков
       - Заголовки должны быть не длиннее 100 символов без хештегов
       - Используйте не более 3 релевантных хештегов
       - Оптимальная температура: 0.7-0.9 для креативности
       - Чем больше задержка между запросами, тем качественнее текст
       - Если текст обрезан - увеличьте задержку
       - Для простых заголовков отключите AI

    🔑 4. Управление ключами:
       - Можно сохранить несколько API ключей
       - При достижении лимита переключитесь на другой ключ
       - Для управления ключами используйте кнопку "Управление"

    📂 5. Редактор файлов:
       - Используйте кнопку "Открыть файл" для просмотра CSV или Excel
       - Редактируйте данные прямо в таблице
       - Используйте поиск для быстрого нахождения информации
       - Сохраняйте изменения кнопкой "Сохранить"

    🐞 6. Отчеты об ошибках:
       - При возникновении ошибки нажмите "Подробнее" для просмотра деталей
       - Используйте меню "Отчеты" для просмотра последней ошибки
       - Отправьте отчет разработчику для быстрого исправления

    💡 7. Советы:
       - Оптимальный интервал между постами: 30-50 минут
       - Лучшее время публикаций: 15:00-21:00 по МСК
       - Используйте перемешивание для A/B тестирования
       - Обновляйте базу пинов раз в 2 недели

    ⚠ 8. Диагностика проблем:
       - Ошибка колонок: проверьте названия столбцов в Excel
       - Пустой результат: ослабьте фильтры сохранений
       - Проблемы с датами: используйте один из стандартных форматов
       - Для больших файлов (>10k строк) ожидайте до 5 мин обработки

    🔒 9. Проверка безопасности:
       - После создания файла выполняется проверка на дубликаты заголовков и ссылок
       - Дубликаты могут привести к блокировке аккаунта Pinterest!

    📞 Поддержка: {app.contact}
    """)

    help_text.insert(tk.INSERT, instructions.strip())
    help_text.configure(state=tk.DISABLED)