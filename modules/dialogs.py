import tkinter as tk
from tkinter import ttk, messagebox
import os
from modules.utils import bind_paste_shortcut
from modules.auth import AuthManager

class LoginDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.auth = app.auth
        self.title("Авторизация")
        self.geometry("400x200")
        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Введите ваш email:").pack(pady=5, anchor=tk.W)

        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(main_frame, textvariable=self.email_var, width=30)
        email_entry.pack(fill=tk.X, pady=5)
        email_entry.focus_set()
        bind_paste_shortcut(email_entry)

        self.save_login_var = tk.BooleanVar(value=True)
        save_cb = ttk.Checkbutton(
            main_frame,
            text="Сохранить вход на этом устройстве",
            variable=self.save_login_var
        )
        save_cb.pack(pady=10, anchor=tk.W)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        login_btn = ttk.Button(
            btn_frame,
            text="Войти",
            command=self.attempt_login,
            width=10
        )
        login_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = ttk.Button(
            btn_frame,
            text="Отмена",
            command=self.destroy,
            width=10
        )
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def attempt_login(self):
        """Попытка авторизации"""
        email = self.email_var.get().strip()
        if not email:
            messagebox.showerror("Ошибка", "Введите email")
            return

        if self.auth.verify_email(email):
            if self.save_login_var.get():
                self.auth.save_login(email)

            self.app.status_var.set(f"Авторизован: {email}")
            self.app.update_menu()

            messagebox.showinfo("Успешно", "Авторизация прошла успешно!")
            self.destroy()
        else:
            messagebox.showerror(
                "Ошибка авторизации",
                "Ваш email не найден в списке разрешенных. Обратитесь к администратору."
            )


class KeyManagementDialog(tk.Toplevel):
    def __init__(self, parent, key_manager, key_var):
        super().__init__(parent)
        self.parent = parent
        self.key_manager = key_manager
        self.key_var = key_var
        self.title("Управление API ключами")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        list_frame = ttk.LabelFrame(main_frame, text="Сохраненные ключи")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.keys_listbox = tk.Listbox(list_frame, height=8)
        self.keys_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.refresh_list()

        self.keys_listbox.bind('<<ListboxSelect>>', self.on_key_select)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        key_entry_frame = ttk.Frame(control_frame)
        key_entry_frame.pack(fill=tk.X, pady=5)
        ttk.Label(key_entry_frame, text="Новый ключ:").pack(side=tk.LEFT, padx=(0, 5))
        self.new_key_var = tk.StringVar()
        new_key_entry = ttk.Entry(key_entry_frame, textvariable=self.new_key_var, width=40)
        new_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        bind_paste_shortcut(new_key_entry)

        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        add_btn = ttk.Button(
            btn_frame,
            text="Добавить",
            command=self.add_key,
            width=10
        )
        add_btn.pack(side=tk.LEFT, padx=2)

        remove_btn = ttk.Button(
            btn_frame,
            text="Удалить",
            command=self.remove_key,
            width=10
        )
        remove_btn.pack(side=tk.LEFT, padx=2)

        select_btn = ttk.Button(
            btn_frame,
            text="Выбрать",
            command=self.select_key,
            width=10
        )
        select_btn.pack(side=tk.LEFT, padx=2)

        close_btn = ttk.Button(
            btn_frame,
            text="Закрыть",
            command=self.destroy,
            width=10
        )
        close_btn.pack(side=tk.RIGHT, padx=2)

    def refresh_list(self):
        """Обновляет список ключей"""
        self.keys_listbox.delete(0, tk.END)
        for key in self.key_manager.get_keys():
            display_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key
            self.keys_listbox.insert(tk.END, display_key)
            self.keys_listbox.itemconfig(tk.END, {'bg': '#f0f0f0'})

    def on_key_select(self, event):
        """Обработчик выбора ключа"""
        selection = self.keys_listbox.curselection()
        if selection:
            idx = selection[0]
            self.key_var.set(self.key_manager.get_keys()[idx])

    def add_key(self):
        """Добавляет новый ключ"""
        key = self.new_key_var.get().strip()
        if not key:
            messagebox.showwarning("Предупреждение", "Введите ключ")
            return

        if self.key_manager.add_key(key):
            self.refresh_list()
            self.new_key_var.set("")
            messagebox.showinfo("Успех", "Ключ успешно добавлен")
        else:
            messagebox.showinfo("Информация", "Ключ уже существует")

    def remove_key(self):
        """Удаляет выбранный ключ"""
        selection = self.keys_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите ключ для удаления")
            return

        idx = selection[0]
        key = self.key_manager.get_keys()[idx]

        if self.key_manager.remove_key(key):
            self.refresh_list()
            messagebox.showinfo("Успех", "Ключ успешно удален")
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить ключ")

    def select_key(self):
        """Выбирает ключ и закрывает диалог"""
        selection = self.keys_listbox.curselection()
        if selection:
            self.destroy()
        else:
            messagebox.showwarning("Предупреждение", "Выберите ключ")