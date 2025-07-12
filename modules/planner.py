import random
import tkinter.messagebox as messagebox
from datetime import datetime, timedelta, time as dt_time

import pandas as pd
import numpy as np

from modules.ai_generator import generate_unique_texts
from modules.utils import convert_to_number, parse_date, check_for_duplicates


class PinterestPlanner:
    def __init__(self, app):
        self.app = app

    def run_planner(self):
        """Запускает процесс генерации расписания публикаций"""
        try:
            self.app.status_var.set("Чтение файла...")
            file_path = self.app.input_file_var.get()

            # Чтение входного файла
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)

            # Проверка обязательных столбцов
            required_columns = ['image url', 'saves', 'created date']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                self.app.status_var.set("Ошибка: отсутствуют столбцы")
                messagebox.showerror(
                    "Ошибка",
                    f"В файле отсутствуют обязательные столбцы:\n\n{', '.join(missing_columns)}\n\n"
                    f"Доступные столбцы: {', '.join(df.columns)}"
                )
                self.app.hide_progress()
                return

            self.app.status_var.set("Обработка дат...")
            current_time = datetime.now()
            date_errors = []

            # Преобразование дат в правильный формат
            date_series = df['created date'].copy()
            converted_dates = pd.Series(index=date_series.index, dtype='datetime64[ns]')

            try:
                converted_dates = pd.to_datetime(date_series, errors='coerce', utc=False)
            except Exception as e:
                self.app.status_var.set(f"Ошибка преобразования: {str(e)}")
                date_errors.append(f"Автоматическое преобразование не удалось: {str(e)}")

            mask = converted_dates.isnull()
            if mask.sum() > 0:
                date_formats = [
                    '%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y',
                    '%Y.%m.%d', '%Y/%m/%d', '%Y-%m-%d',
                    '%d.%m.%y', '%d/%m/%y', '%d-%m-%y',
                    '%d %b %Y', '%d %B %Y'
                ]
                for fmt in date_formats:
                    if mask.sum() == 0:
                        break
                    try:
                        # Создаем временную серию для преобразования
                        temp_series = pd.Series(date_series[mask])
                        partial = pd.to_datetime(temp_series, format=fmt, errors='coerce', utc=False)

                        # Обновляем только успешно преобразованные значения
                        success_mask = ~partial.isnull()
                        converted_dates.loc[mask] = partial

                        # Обновляем маску для оставшихся значений
                        mask = converted_dates.isnull()
                    except:
                        continue

            df['created date'] = converted_dates

            # Проверка на некорректные даты
            invalid_mask = df['created date'].isnull()
            if invalid_mask.any():
                invalid_count = invalid_mask.sum()
                invalid_samples = date_series[invalid_mask].head(5).tolist()

                error_details = (
                    f"Найдены {invalid_count} некорректных дат в столбце created date.\n"
                    f"Примеры некорректных значений:\n{invalid_samples}\n\n"
                    "Убедитесь, что все даты в одном из форматов:\n"
                    "ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ, ГГГГ.ММ.ДД"
                )

                self.app.status_var.set("Ошибка: неверный формат даты")
                messagebox.showerror("Ошибка формата даты", error_details)
                self.app.hide_progress()
                return

            # Удаление часового пояса (если присутствует)
            try:
                # Проверяем, есть ли хотя бы одно значение с часовым поясом
                if any(ts.tz is not None for ts in df['created date'] if pd.notnull(ts)):
                    df['created date'] = df['created date'].dt.tz_convert(None)
            except (TypeError, AttributeError):
                # Игнорируем ошибки если столбец не содержит datetime или tz
                pass

            # Расчет весов для сортировки
            if not self.app.sort_by_saves_only.get():
                # Используем .dt.days вместо .dt.total_seconds()
                df['days_passed'] = (current_time - df['created date']).dt.days
                df['weight'] = df['saves'] / (df['days_passed'] + 1)
                df = df.sort_values(by='weight', ascending=False)
            else:
                df = df.sort_values(by='saves', ascending=False)

            # Применение фильтров
            if self.app.enable_min_saves.get():
                min_saves = convert_to_number(self.app.min_saves_var.get())
                if min_saves is not None and 'saves' in df.columns:
                    df = df[df['saves'] >= min_saves]

            if self.app.enable_post_limit.get():
                post_limit = convert_to_number(self.app.post_limit_var.get())
                if post_limit is not None:
                    df = df.head(post_limit)

            # Проверка на пустой результат
            if df.empty:
                messagebox.showwarning("Предупреждение", "Нет данных для генерации расписания.")
                self.app.status_var.set("Нет данных")
                self.app.hide_progress()
                return

            self.app.status_var.set("Генерация текстов...")
            count = len(df)

            # Callback для обновления прогресса
            def update_progress(current, total):
                progress = (current / total) * 100
                self.app.root.after(0, self.app.update_progress_bar, progress, current, total)

            # Генерация текстов и ссылок
            base_text = self.app.base_text_var.get()
            base_link = self.app.base_link_var.get()

            texts = generate_unique_texts(self.app, base_text, count, update_progress)
            links = self.generate_unique_links(base_link, count)

            df['text'] = texts
            df['link'] = links

            # Проверка на дубликаты
            duplicates_found = check_for_duplicates(df)

            # Подготовка дат публикаций
            start_date = parse_date(self.app.date_var.get())
            start_time = self.app.time_var.get()
            min_interval = int(self.app.min_interval_var.get())
            max_interval = int(self.app.max_interval_var.get())

            try:
                start_hour, start_minute = map(int, start_time.split(':'))
                start_datetime = datetime.combine(start_date, dt_time(start_hour, start_minute))
            except Exception:
                start_datetime = datetime.combine(start_date, dt_time(12, 0))

            # Создание выходного DataFrame
            df_output = pd.DataFrame({
                'text': df['text'],
                'link': df['link'],
                'image1': df['image url']
            })

            # Перемешивание, если нужно
            if self.app.shuffle_var.get():
                df_output = df_output.sample(frac=1).reset_index(drop=True)

            # Генерация дат публикаций
            datetimes = []
            current = start_datetime

            for i in range(len(df_output)):
                datetimes.append(current)
                interval = random.randint(min_interval, max_interval)
                current += timedelta(minutes=interval)

            df_output['date'] = [dt.strftime('%d.%m.%Y %H:%M') for dt in datetimes]

            # Сохранение результата
            output_path = self.app.output_file_var.get()
            df_output[['date', 'text', 'link', 'image1']].to_csv(output_path, index=False)

            self.app.status_var.set(f"Готово! Сгенерировано {len(df)} записей")
            self.app.hide_progress()
            messagebox.showinfo("Успешно", f"Файл сохранен: {output_path}")

        except Exception as e:
            self.app.status_var.set("Ошибка!")
            self.app.hide_progress()
            self.app.log_error(e)
            self.app.show_error_with_details(e)

    def generate_unique_links(self, base_link, count):
        """Генерирует уникальные ссылки для постов"""
        base_link = base_link.rstrip('/')
        if self.app.advanced_mode.get() and self.app.link_template_var.get():
            template = self.app.link_template_var.get()
            return [f"{base_link}{template.replace('{num}', str(101 + i))}" for i in range(count)]
        return [f"{base_link}/?{101 + i}" for i in range(count)]