import re
import time
import tkinter.messagebox as messagebox
from openai import OpenAI, AuthenticationError, RateLimitError, APIError, APIConnectionError

from modules.utils import log_error


def parse_ai_response(response, count):
    """Парсит ответ AI в список текстов"""
    texts = []
    # Пытаемся извлечь пронумерованные варианты
    for i in range(1, count + 1):
        pattern = re.compile(rf"{i}\.\s*(.+)")
        match = pattern.search(response)
        if match:
            text = match.group(1).strip()
            if text and text[-1] not in ['.', '!', '?']:
                text += '...'
            texts.append(text)
        else:
            break

    # Если не нашли достаточно вариантов, пробуем извлечь строки
    if len(texts) < count:
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        for line in lines:
            if line not in texts and not re.match(r'^\d+\.', line):
                if line and line[-1] not in ['.', '!', '?']:
                    line += '...'
                texts.append(line)
                if len(texts) >= count:
                    break

    return texts[:count]


def generate_with_openrouter(app, base_text, count, progress_callback=None):
    """Генерация текстов через OpenRouter API"""
    api_key = app.openrouter_key_var.get()
    if not api_key:
        return generate_standard_texts(base_text, count, progress_callback)

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/pinterest-planner",
                "X-Title": "Pinterest Planner"
            }
        )

        prompt = f"""
        Сгенерируй {count} уникальных вариантов текста для пинов в Pinterest на тему:
        "{base_text}"

        Требования:
        1. Каждый текст должен быть уникальным и не повторять другие варианты
        2. Длина текста: не более 100 символов (без хештегов)
        3. Не используй хештеги
        4. Включи призыв к действию (например: "Узнай больше", "Скачай сейчас")
        5. Пронумеруй варианты как: 1. [текст], 2. [текст], и т.д.
        6. Сохрани маркетинговый стиль и тональность
        7. Убедись, что текст завершен и имеет смысл
        """

        temperature = app.openrouter_temperature_var.get()
        max_tokens = app.openrouter_max_tokens_var.get()
        model = app.openrouter_model_var.get()

        try:
            delay_val = float(app.openrouter_delay_var.get())
        except:
            delay_val = 5.0
        delay = max(5.0, delay_val)

        batch_size = 10
        texts = []
        for i in range(0, count, batch_size):
            current_count = min(batch_size, count - i)
            current_prompt = prompt.replace(f"{count}", f"{current_count}")

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": current_prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                full_response = response.choices[0].message.content.strip()
                batch_texts = parse_ai_response(full_response, current_count)
                texts.extend(batch_texts)

                # Обновляем прогресс
                current_progress = i + len(batch_texts)
                if progress_callback:
                    progress_callback(current_progress, count)

                time.sleep(delay)
            except Exception as e:
                app.status_var.set(f"Ошибка генерации: {str(e)}")
                # Логируем ошибку, но продолжаем генерацию
                log_error(e, app)

        # Если сгенерировали меньше текстов, чем нужно
        if len(texts) < count:
            last_text = texts[-1] if texts else base_text
            additional = generate_standard_texts(last_text, count - len(texts), None)
            texts.extend(additional)

        return texts[:count]

    except Exception as e:
        error_msg = f"Ошибка при генерации текстов через OpenRouter: {str(e)}"
        app.status_var.set(error_msg)
        app.log_error(e)
        messagebox.showwarning(
            "Ошибка генерации",
            f"{error_msg}\n\nТексты сгенерированы стандартным методом."
        )
        return generate_standard_texts(base_text, count, progress_callback)

    pass


def generate_with_chatgpt(app, base_text, count, progress_callback=None):
    """Генерация текстов через ChatGPT API"""
    api_key = app.api_key_var.get()
    if not api_key:
        return generate_standard_texts(base_text, count, progress_callback)

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
        Сгенерируй {count} уникальных вариантов текста для пинов в Pinterest на тему:
        "{base_text}"

        Требования:
        1. Каждый текст должен быть уникальным и не повторять другие варианты
        2. Длина текста: не более 100 символов (без хештегов)
        3. Не используй хештеги
        4. Включи призыв к действию (например: "Узнай больше", "Скачай сейчас")
        5. Пронумеруй варианты как: 1. [текст], 2. [текст], и т.д.
        6. Сохрани маркетинговый стиль и тональность
        7. Убедись, что текст завершен и имеет смысл
        """

        temperature = app.ai_temperature_var.get()
        max_tokens = app.ai_max_tokens_var.get()
        model = app.ai_model_var.get()

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )

            full_response = response.choices[0].message.content.strip()
            texts = parse_ai_response(full_response, count)

            # Обновляем прогресс
            if progress_callback:
                progress_callback(len(texts), count)

            # Если сгенерировали меньше текстов, чем нужно
            if len(texts) < count:
                last_text = texts[-1] if texts else base_text
                additional = generate_standard_texts(last_text, count - len(texts), None)
                texts.extend(additional)

            return texts

        except RateLimitError as e:
            error_msg = "Превышен лимит запросов к ChatGPT API!"
            app.status_var.set(error_msg)
            app.log_error(e)
            messagebox.showwarning(
                "Ошибка лимита",
                f"{error_msg}\nПожалуйста, подождите или используйте другой API ключ."
            )
            return generate_standard_texts(base_text, count, progress_callback)

        except AuthenticationError as e:
            error_msg = "Ошибка аутентификации ChatGPT API!"
            app.status_var.set(error_msg)
            app.log_error(e)
            messagebox.showwarning(
                "Ошибка аутентификации",
                f"{error_msg}\nПроверьте правильность API ключа."
            )
            return generate_standard_texts(base_text, count, progress_callback)

        except Exception as e:
            error_msg = f"Ошибка при генерации текстов через ChatGPT: {str(e)}"
            app.status_var.set(error_msg)
            app.log_error(e)
            messagebox.showwarning(
                "Ошибка генерации",
                f"{error_msg}\nТексты сгенерированы стандартным методом."
            )
            return generate_standard_texts(base_text, count, progress_callback)

    except Exception as e:
        error_msg = f"Критическая ошибка при подключении к ChatGPT: {str(e)}"
        app.status_var.set(error_msg)
        app.log_error(e)
        messagebox.showerror(
            "Ошибка подключения",
            f"{error_msg}\nПроверьте подключение к интернету и настройки API."
        )
        return generate_standard_texts(base_text, count, progress_callback)


    pass


def generate_standard_texts(base_text, count, progress_callback=None):
    """Генерация стандартных текстов с нумерацией"""
    texts = []
    for i in range(count):
        texts.append(f"{base_text} #{101 + i}")
        if progress_callback:
            progress_callback(i + 1, count)
    return texts


def generate_unique_texts(app, base_text, count, progress_callback=None):
    """Генерация уникальных текстов с возможностью использования AI"""
    if app.use_openrouter_var.get() and app.openrouter_key_var.get():
        try:
            return generate_with_openrouter(app, base_text, count, progress_callback)
        except Exception as e:
            messagebox.showwarning(
                "Ошибка OpenRouter",
                f"Не удалось сгенерировать тексты: {str(e)}. Используется базовый метод."
            )

    if app.ai_enabled.get() and app.api_key_var.get():
        try:
            return generate_with_chatgpt(app, base_text, count, progress_callback)
        except Exception as e:
            messagebox.showwarning(
                "Ошибка AI",
                f"Не удалось сгенерировать тексты: {str(e)}. Используется базовый метод."
            )

    if app.advanced_mode.get() and app.text_template_var.get():
        template = app.text_template_var.get()
        return [template.replace('{num}', str(101 + i)) for i in range(count)]

    return generate_standard_texts(base_text, count, progress_callback)