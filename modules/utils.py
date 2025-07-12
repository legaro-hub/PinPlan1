import re
import os
import platform
import socket
import traceback
import json
import tkinter as tk
from datetime import datetime
from config import LOG_FILE

def handle_paste(event):
    if event.state & 4:
        keycode = getattr(event, 'keycode', None)
        keysym = event.keysym.lower()
        if (keycode == 86) or (keysym == 'v') or (keysym == 'м'):
            try:
                root = event.widget.winfo_toplevel()
                clipboard_text = root.clipboard_get()
                event.widget.insert(tk.INSERT, clipboard_text)
                return 'break'
            except tk.TclError:
                pass
    return None

def bind_paste_shortcut(widget):
    widget.bind("<Control-KeyPress>", handle_paste)

def handle_hotkeys(event, table):
    keycode = getattr(event, 'keycode', None)
    keysym = event.keysym.lower()
    if event.state & 0x0004:
        if keycode == 86 or keysym == 'v' or keysym == 'м':
            table.paste()
            return "break"
        elif keycode == 67 or keysym == 'c' or keysym == 'с':
            table.copy()
            return "break"
        elif keycode == 88 or keysym == 'x' or keysym == 'ч':
            table.cut()
            return "break"
    return None

def convert_to_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%d%m%Y").date()
        except ValueError:
            return datetime.now().date()

def format_date_input(event, date_var):
    current = date_var.get()
    cursor_pos = event.widget.index(tk.INSERT)
    clean = re.sub(r'[^\d]', '', current)
    if len(clean) > 8: clean = clean[:8]
    if len(clean) == 8:
        formatted = f"{clean[:2]}.{clean[2:4]}.{clean[4:]}"
        date_var.set(formatted)
        event.widget.icursor(tk.END)
    else:
        date_var.set(clean)
        event.widget.icursor(cursor_pos)

def format_time_input(event, time_var):
    current = time_var.get()
    cursor_pos = event.widget.index(tk.INSERT)
    clean = re.sub(r'[^\d]', '', current)
    if len(clean) > 4: clean = clean[:4]
    if len(clean) == 4:
        formatted = f"{clean[:2]}:{clean[2:]}"
        time_var.set(formatted)
        event.widget.icursor(tk.END)
    else:
        time_var.set(clean)
        event.widget.icursor(cursor_pos)

def correct_delay_value(delay_var):
    try:
        value = float(delay_var.get())
        if value < 5.0: delay_var.set(5.0)
    except: delay_var.set(5.0)

def toggle_advanced_settings(frame, advanced_mode):
    if advanced_mode.get(): frame.pack(fill=tk.X, padx=5, pady=5)
    else: frame.pack_forget()

def toggle_openrouter_settings(frame, use_openrouter_var):
    if use_openrouter_var.get(): frame.pack(fill=tk.X, padx=5, pady=5)
    else: frame.pack_forget()

def toggle_ai_settings(frame, ai_enabled):
    if ai_enabled.get(): frame.pack(fill=tk.X, padx=5, pady=5)
    else: frame.pack_forget()

def toggle_entry_state(entry, var):
    if var.get(): entry.config(state=tk.NORMAL)
    else: entry.config(state=tk.DISABLED)

def update_openai_keys(combo, key_manager, key_var):
    keys = key_manager.get_keys()
    display_keys = [f"{k[:8]}...{k[-4:]}" if len(k) > 12 else k for k in keys]
    combo['values'] = display_keys
    if keys: key_var.set(keys[0])

def update_openrouter_keys(combo, key_manager, key_var):
    keys = key_manager.get_keys()
    display_keys = [f"{k[:8]}...{k[-4:]}" if len(k) > 12 else k for k in keys]
    combo['values'] = display_keys
    if keys: key_var.set(keys[0])

def check_for_duplicates(df):
    duplicates = False
    if df['text'].duplicated().any():
        dup_text = df[df['text'].duplicated(keep=False)]
        duplicates = True
    if df['link'].duplicated().any():
        dup_links = df[df['link'].duplicated(keep=False)]
        duplicates = True
    return duplicates

def log_error(exception, app):
    error_info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": app.version,
        "input_file": app.input_file_var.get(),
        "output_file": app.output_file_var.get(),
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "traceback": traceback.format_exc(),
        "auth_user": app.auth.current_user or "none"
    }
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                try: logs = json.load(f)
                except: pass
        logs.append(error_info)
        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        app.last_error = error_info
    except Exception as e:
        print(f"Ошибка при записи лога: {str(e)}")