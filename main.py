import sys
import os
import tkinter as tk

# Добавляем пути для корректного импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app_ui import PinterestPlannerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = PinterestPlannerApp(root)

    # Настройка иконки приложения
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass

    root.mainloop()