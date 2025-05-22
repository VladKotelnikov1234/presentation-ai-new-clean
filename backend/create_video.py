import requests
import time
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# API ключ для Shotstack (замените на свой)
SHOTSTACK_API_KEY = "pI20Mwb2fkPETNU1FUNwij6xQA6aEdhb2kZ0JfXw"

# Настройка Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDS_FILE = "credentials.json"  # Файл с учётными данными Google Drive API
TOKEN_FILE = "token.json"  # Файл токена создаётся автоматически

# Проверка наличия credentials.json
if not os.path.exists(CREDS_FILE):
    raise FileNotFoundError(
        f"Файл {CREDS_FILE} не найден. Создайте его через Google Cloud Console:\n"
        "1. Включите Google Drive API.\n"
        "2. Создайте OAuth 2.0 Client ID (Desktop App).\n"
        "3. Скачайте JSON-файл и переименуйте его в 'credentials.json'."
    )

def get_drive_service():
    """Инициализация Google Drive API."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def upload_to_drive(file_path, file_name):
    """Загрузка файла на Google Drive и получение публичного URL."""
    service = get_drive_service()
    file_metadata = {"name": file_name}
    media = MediaFileUpload(file_path)
    file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = file.get("id")

    # Делаем файл публичным
    permission = {"type": "anyone", "role": "reader"}
    service.permissions().create(fileId=file_id, body=permission).execute()

    # Получаем публичный URL
    file_url = f"https://drive.google.com/uc?id={file_id}"
    print(f"Файл загружен на Google Drive: {file_url}")
    return file_url

def create_srt_file():
    """Создание SRT-файла для субтитров."""
    srt_content = (
        "1\n00:00:00,000 --> 00:00:05,000\nЗдравствуйте, друзья! Добро пожаловать в мир программирования,\n\n"
        "2\n00:00:05,001 --> 00:00:10,000\nгде идеи оживают через код. Представьте: вы создаёте программу,\n\n"
        "3\n00:00:10,001 --> 00:00:15,000\nкоторая управляет электросетями или автоматизирует процессы.\n\n"
        "4\n00:00:15,001 --> 00:00:20,000\nС чего начать? Всё начинается с алгоритма — пошаговой инструкции,\n\n"
        "5\n00:00:20,001 --> 00:00:25,000\nкоторая решает задачу. Алгоритм должен быть точным, понятным\n\n"
        "6\n00:00:25,001 --> 00:00:30,000\nи конечным, с такими свойствами, как дискретность и детерминированность.\n\n"
        "7\n00:00:30,001 --> 00:00:35,000\nНапример, чтобы забить гвоздь, вы берёте молоток, бьёте и повторяете.\n\n"
        "8\n00:00:35,001 --> 00:00:40,000\nВ программировании мы используем блок-схемы: следование, ветвление и циклы.\n\n"
        "9\n00:00:40,001 --> 00:00:45,000\nСледование — это шаги один за другим, ветвление — выбор пути,\n\n"
        "10\n00:00:45,001 --> 00:00:50,000\nа циклы — повторение действий. Освойте их, и вы сможете писать программы.\n\n"
        "11\n00:00:50,001 --> 00:00:55,000\nНачните с простого: вычислите сумму трёх чисел или найдите наибольшее.\n\n"
        "12\n00:00:55,001 --> 00:01:00,000\nЗатем переходите к циклам, чтобы посчитать сумму ряда.\n\n"
        "13\n00:01:00,001 --> 00:01:05,000\nПрограммирование — это мышление: учитесь анализировать задачи,\n\n"
        "14\n00:01:05,001 --> 00:01:10,000\nразбивать их на части и находить решения.\n\n"
        "15\n00:01:10,001 --> 00:01:30,000\nДавайте начнём этот путь вместе, шаг за шагом, создавая программы, которые изменят мир!\n"
    )
    srt_file = "subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print("SRT-файл создан: subtitles.srt")
    return srt_file

def create_video(srt_url):
    """Создание видео через Shotstack API без озвучки."""
    url = "https://api.shotstack.io/v1/render"
    headers = {
        "Authorization": f"Bearer {SHOTSTACK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "timeline": {
            "fonts": [
                {
                    "src": "https://shotstack-assets.s3-ap-southeast-2.amazonaws.com/fonts/Montserrat-ExtraBold.ttf"
                }
            ],
            "tracks": [
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "caption",
                                "src": srt_url,
                                "font": {
                                    "color": "#ffffff",
                                    "family": "Montserrat ExtraBold",
                                    "size": 30,
                                    "lineHeight": 0.8
                                },
                                "background": {
                                    "color": "#000000",
                                    "padding": 20,
                                    "borderRadius": 18,
                                    "opacity": 0.6
                                },
                                "margin": {
                                    "top": 0.25,
                                    "left": 0.05,
                                    "right": 0.05
                                }
                            },
                            "start": 0,
                            "length": 90  # Длительность видео 90 секунд
                        }
                    ]
                },
                {
                    "clips": [
                        {
                            "asset": {
                                "type": "video",
                                "src": "https://shotstack-assets.s3.amazonaws.com/footage/night-sky.mp4"
                            },
                            "start": 0,
                            "length": 90
                        }
                    ]
                }
            ]
        },
        "output": {
            "format": "mp4",
            "resolution": "fhd",  # Full HD (1920x1080)
            "size": {
                "width": 1920,
                "height": 1080
            }
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    render_id = response.json()["response"]["id"]
    print(f"Видео отправлено на рендеринг, ID: {render_id}")
    return render_id

def check_render_status(render_id):
    """Проверка статуса рендеринга и получение URL готового видео."""
    url = f"https://api.shotstack.io/v1/render/{render_id}"
    headers = {
        "Authorization": f"Bearer {SHOTSTACK_API_KEY}",
        "Content-Type": "application/json"
    }
    while True:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        status = response.json()["response"]["status"]
        print(f"Статус рендеринга: {status}")
        if status == "done":
            video_url = response.json()["response"]["url"]
            print(f"Видео готово! URL: {video_url}")
            return video_url
        elif status in ["failed", "error"]:
            raise Exception("Ошибка рендеринга")
        time.sleep(10)  # Проверяем каждые 10 секунд

def download_video(video_url):
    """Скачивание готового видео."""
    response = requests.get(video_url)
    with open("programming_video.mp4", "wb") as f:
        f.write(response.content)
    print("Видео скачано: programming_video.mp4")

# Выполнение
if __name__ == "__main__":
    # Создаём SRT-файл
    srt_file = create_srt_file()

    # Загружаем SRT-файл на Google Drive
    srt_url = upload_to_drive(srt_file, "subtitles.srt")

    # Создаём видео (без озвучки, 1920x1080)
    render_id = create_video(srt_url)

    # Проверяем статус и скачиваем
    video_url = check_render_status(render_id)
    download_video(video_url)