import os
import tkinter.messagebox as messagebox
from config import LOGIN_FILE, ALLOWED_FILE

class AuthManager:
    def __init__(self):
        self.login_file = LOGIN_FILE
        self.allowed_file = ALLOWED_FILE
        self.current_user = None
        self.create_allowed_file()

    def create_allowed_file(self):
        if not os.path.exists(self.allowed_file):
            with open(self.allowed_file, "w") as f:
                f.write("legaro.hub@gmail.com\n")

    def check_authorization(self):
        if os.path.exists(self.login_file):
            try:
                with open(self.login_file, "r") as f:
                    email = f.read().strip()
                    if email:
                        return self.verify_email(email)
            except Exception as e:
                print(f"Ошибка чтения файла авторизации: {str(e)}")
        return False

    def verify_email(self, email):
        email = email.strip().lower()
        if not os.path.exists(self.allowed_file):
            return False

        try:
            with open(self.allowed_file, "r") as f:
                allowed_emails = [line.strip().lower() for line in f.readlines()]
                if email in allowed_emails:
                    self.current_user = email
                    return True
        except Exception as e:
            print(f"Ошибка проверки email: {str(e)}")
        return False

    def save_login(self, email):
        try:
            with open(self.login_file, "w") as f:
                f.write(email)
            return True
        except Exception as e:
            print(f"Ошибка сохранения авторизации: {str(e)}")
            return False

    def logout(self):
        try:
            if os.path.exists(self.login_file):
                os.remove(self.login_file)
            self.current_user = None
            return True
        except Exception as e:
            print(f"Ошибка выхода из системы: {str(e)}")
            return False