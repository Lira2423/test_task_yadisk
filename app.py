import os
from typing import Dict, List, Any
from flask import Flask, render_template, request, redirect, url_for, send_file
import requests

app = Flask(__name__)
YANDEX_DISK_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"

# Вспомогательная функция для получения списка файлов по public_key
def get_files_from_yandex_disk(public_key: str) -> List[Dict[str, Any]]:
    params = {"public_key": public_key, "limit": 100}  # Лимит на количество файлов
    response = requests.get(YANDEX_DISK_API_URL, params=params)
    if response.status_code == 200:
        return response.json().get("_embedded", {}).get("items", [])
    else:
        raise Exception(f"Ошибка при получении данных: {response.status_code}")

# Вспомогательная функция для скачивания файла
def download_file_from_yandex_disk(file_url: str, file_name: str) -> str:
    response = requests.get(file_url, stream=True)
    if response.status_code == 200:
        local_path = os.path.join("downloads", file_name)
        os.makedirs("downloads", exist_ok=True)
        with open(local_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return local_path
    else:
        raise Exception(f"Ошибка при скачивании файла: {response.status_code}")

# Функция для определения типа файла по расширению
def get_file_type(file_name: str) -> str:
    extension = os.path.splitext(file_name)[1].lower()
    if extension in ['.jpg', '.jpeg', '.png', '.gif']:
        return 'Изображение'
    elif extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        return 'Документ'
    elif extension in ['.mp3', '.wav', '.flac']:
        return 'Аудио'
    elif extension in ['.mp4', '.avi', '.mkv']:
        return 'Видео'
    elif extension in ['.txt']:
        return 'Текстовый файл'
    else:
        return 'Неизвестный тип'

# Главная страница
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        public_key = request.form.get("public_key")
        try:
            files = get_files_from_yandex_disk(public_key)
            # Добавляем тип файла к каждому элементу
            for file in files:
                if file['type'] == 'file':
                    file['file_type'] = get_file_type(file['name'])
                else:
                    file['file_type'] = 'Папка'
            return render_template("files.html", files=files, public_key=public_key)
        except Exception as e:
            return render_template("index.html", error=str(e))
    return render_template("index.html")

# Скачивание файла
@app.route("/download/<path:file_url>/<file_name>")
def download(file_url: str, file_name: str):
    try:
        local_path = download_file_from_yandex_disk(file_url, file_name)
        return send_file(local_path, as_attachment=True)
    except Exception as e:
        return f"Ошибка при скачивании файла: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)