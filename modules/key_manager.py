import json
import os

class KeyManager:
    def __init__(self, filename):
        self.filename = filename
        self.keys = []
        self.load_keys()

    def load_keys(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self.keys = json.load(f)
            except:
                self.keys = []

    def save_keys(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.keys, f, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения ключей: {str(e)}")
            return False

    def add_key(self, key):
        if key not in self.keys:
            self.keys.append(key)
            self.save_keys()
            return True
        return False

    def remove_key(self, key):
        if key in self.keys:
            self.keys.remove(key)
            self.save_keys()
            return True
        return False

    def get_keys(self):
        return self.keys