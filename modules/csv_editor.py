import pandas as pd
import os
import tkinter as tk
from tkinter import ttk, messagebox  # Добавлен импорт ttk
from pandastable import Table, TableModel
from modules.utils import bind_paste_shortcut, handle_hotkeys


class CSVEditor:
    def __init__(self, parent, file_path):
        self.parent = parent
        self.file_path = file_path
        self.create_editor()

    def create_editor(self):
        """Создает окно редактора CSV/Excel файлов"""
        self.editor = tk.Toplevel(self.parent)
        self.editor.title(f"Редактор: {os.path.basename(self.file_path)}")
        self.editor.geometry("1200x800")

        control_frame = ttk.Frame(self.editor, padding=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Кнопки управления
        save_btn = ttk.Button(
            control_frame,
            text="Сохранить",
            command=self.save_csv
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        refresh_btn = ttk.Button(
            control_frame,
            text="Обновить",
            command=self.refresh_table
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Поиск
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.RIGHT, padx=10)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        bind_paste_shortcut(search_entry)
        search_entry.bind("<KeyRelease>", lambda e: self.search_in_table(self.search_var.get()))

        # Область таблицы
        table_frame = ttk.Frame(self.editor)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        try:
            # Чтение файла
            if self.file_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            else:
                self.df = pd.read_excel(self.file_path)

            # Проверка обязательных колонок
            required_columns = ['date', 'text', 'link', 'image1']
            for col in required_columns:
                if col not in self.df.columns:
                    self.df[col] = ""

            # Создание таблицы
            self.table = Table(table_frame, dataframe=self.df, showtoolbar=True, showstatusbar=True)
            self.table.show()
            self.table.autoResizeColumns()

            # Привязка горячих клавиш
            self.editor.bind('<Control-KeyPress>', lambda e: handle_hotkeys(e, self.table))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n\n{str(e)}", parent=self.editor)
            self.editor.destroy()

    def save_csv(self):
        """Сохраняет изменения в файл"""
        try:
            self.df = self.table.model.df

            # Проверка обязательных колонок
            required_columns = ['date', 'text', 'link', 'image1']
            for col in required_columns:
                if col not in self.df.columns:
                    self.df[col] = ""

            # Сохранение в правильном формате
            if self.file_path.endswith('.csv'):
                self.df.to_csv(self.file_path, index=False)
            else:
                self.df.to_excel(self.file_path, index=False)

            messagebox.showinfo("Сохранено", "Файл успешно сохранен!", parent=self.editor)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n\n{str(e)}", parent=self.editor)

    def refresh_table(self):
        """Обновляет таблицу из файла"""
        try:
            if self.file_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            else:
                self.df = pd.read_excel(self.file_path)

            # Проверка обязательных колонок
            required_columns = ['date', 'text', 'link', 'image1']
            for col in required_columns:
                if col not in self.df.columns:
                    self.df[col] = ""

            self.table.updateModel(TableModel(self.df))
            self.table.redraw()
            self.table.autoResizeColumns()
            messagebox.showinfo("Обновлено", "Данные успешно обновлены из файла!", parent=self.editor)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить данные:\n\n{str(e)}", parent=self.editor)

    def search_in_table(self, search_text):
        """Поиск текста в таблице"""
        if not search_text:
            self.table.clearSelected()
            return

        df = self.table.model.df
        search_text = search_text.lower()

        self.table.clearSelected()
        self.table.setSelectedCells([])

        matches = []
        for row_idx in range(len(df)):
            for col_idx, col_name in enumerate(df.columns):
                cell_value = str(df.iloc[row_idx, col_idx]).lower()
                if search_text in cell_value:
                    matches.append((row_idx, col_idx))

        if matches:
            self.table.setSelectedCells(matches)
            self.table.see(row=matches[0][0], col=matches[0][1])
        else:
            self.table.clearSelected()