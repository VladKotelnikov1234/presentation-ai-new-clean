import requests
import logging
import os
import time
from django.views import View
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from mutagen.mp3 import MP3

# Настройка логирования
logger = logging.getLogger(__name__)
os.makedirs('media/logs', exist_ok=True)
handler = logging.FileHandler('media/logs/debug_new.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Настройки JSON2Video
JSON2VIDEO_API_KEY = "JSByFMTvHB8CnagNQHh9MbOXV1acaLj0AAftXqgP"
OUTPUT_DIR = 'media/outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Проверка длительности аудио
def get_audio_durations():
    audio_files = [
        "C:/Videos/Audio/scene1.mp3",
        "C:/Videos/Audio/scene2.mp3",
        "C:/Videos/Audio/scene3.mp3",
        "C:/Videos/Audio/scene4.mp3",
        "C:/Videos/Audio/scene5.mp3"
    ]
    durations = []
    for file in audio_files:
        try:
            audio = MP3(file)
            duration = audio.info.length
            durations.append(duration)
            logger.info(f"Длительность {file}: {duration:.2f} секунд")
        except Exception as e:
            logger.error(f"Ошибка при чтении {file}: {e}")
            durations.append(0)
    return durations

# JSON для видео
def get_video_json():
    durations = get_audio_durations()  # Получаем длительности
    return {
        "project": {
            "name": "Programming_Lesson",
            "width": 1920,
            "height": 1080,
            "duration": sum(durations) if all(durations) else 360,  # Общая длительность по аудио
            "scenes": [
                {
                    "id": "intro",
                    "duration": durations[0] if durations[0] else 30,
                    "elements": [
                        {
                            "type": "video",
                            "src": "stock://tech_computer?theme=programming",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "animation": "fadeIn",
                            "animation_duration": 2
                        },
                        {
                            "type": "text",
                            "content": "Программирование — язык технологий",
                            "x": 960,
                            "y": 540,
                            "width": 1200,
                            "font": "Arial",
                            "font_size": 80,
                            "color": "#FFFFFF",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 2,
                            "start_time": 2,
                            "duration": durations[0] - 4 if durations[0] else 26
                        },
                        {
                            "type": "text",
                            "content": "Добро пожаловать на наш урок по основам программирования! Сегодня мы разберём, что такое алгоритмизация и как она помогает компьютеру решать сложные задачи.",
                            "x": 100,
                            "y": 900,
                            "width": 1720,
                            "font": "Arial",
                            "font_size": 40,
                            "color": "#FFFFFF",
                            "background_color": "rgba(0,0,0,0.7)",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 1,
                            "start_time": 4,
                            "duration": durations[0] - 6 if durations[0] else 24
                        },
                        {
                            "type": "audio",
                            "src": "file://C:/Videos/Audio/scene1.mp3",
                            "start_time": 0,
                            "volume": 1.0
                        }
                    ]
                },
                {
                    "id": "algorithm",
                    "duration": durations[1] if durations[1] else 90,
                    "elements": [
                        {
                            "type": "video",
                            "src": "stock://chalkboard?theme=education",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "animation": "fadeIn",
                            "animation_duration": 2
                        },
                        {
                            "type": "image",
                            "src": "stock://flowchart_sum?theme=programming",
                            "x": 960,
                            "y": 540,
                            "width": 800,
                            "height": 600,
                            "animation": "fadeIn",
                            "animation_duration": 2,
                            "start_time": durations[1] - 30 if durations[1] else 60,
                            "duration": 30
                        },
                        {
                            "type": "text",
                            "content": "Алгоритм — это чёткая последовательность шагов, которая превращает исходные данные в нужный результат. Например, чтобы приготовить чай, вы кипятите воду, кладёте заварку, заливаете кипяток и ждёте.",
                            "x": 100,
                            "y": 900,
                            "width": 1720,
                            "font": "Arial",
                            "font_size": 40,
                            "color": "#FFFFFF",
                            "background_color": "rgba(0,0,0,0.7)",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 1,
                            "start_time": 2,
                            "duration": durations[1] - 2 if durations[1] else 88
                        },
                        {
                            "type": "audio",
                            "src": "file://C:/Videos/Audio/scene2.mp3",
                            "start_time": 0,
                            "volume": 1.0
                        }
                    ]
                },
                {
                    "id": "program",
                    "duration": durations[2] if durations[2] else 90,
                    "elements": [
                        {
                            "type": "video",
                            "src": "stock://coding?theme=tech",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "animation": "fadeIn",
                            "animation_duration": 2
                        },
                        {
                            "type": "image",
                            "src": "stock://pascal_code?theme=programming",
                            "x": 960,
                            "y": 540,
                            "width": 800,
                            "height": 400,
                            "animation": "fadeIn",
                            "animation_duration": 2,
                            "start_time": durations[2] - 30 if durations[2] else 60,
                            "duration": 30
                        },
                        {
                            "type": "text",
                            "content": "Алгоритм — это план, а программа — его воплощение. Программа — это команды на языке, который понимает компьютер, например, Pascal.",
                            "x": 100,
                            "y": 900,
                            "width": 1720,
                            "font": "Arial",
                            "font_size": 40,
                            "color": "#FFFFFF",
                            "background_color": "rgba(0,0,0,0.7)",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 1,
                            "start_time": 2,
                            "duration": durations[2] - 2 if durations[2] else 88
                        },
                        {
                            "type": "audio",
                            "src": "file://C:/Videos/Audio/scene3.mp3",
                            "start_time": 0,
                            "volume": 1.0
                        }
                    ]
                },
                {
                    "id": "constructs",
                    "duration": durations[3] if durations[3] else 90,
                    "elements": [
                        {
                            "type": "video",
                            "src": "stock://tech_blocks?theme=education",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "animation": "fadeIn",
                            "animation_duration": 2
                        },
                        {
                            "type": "image",
                            "src": "stock://flowchart_sequence?theme=programming",
                            "x": 640,
                            "y": 360,
                            "width": 400,
                            "height": 300,
                            "animation": "fadeIn",
                            "animation_duration": 2,
                            "start_time": durations[3] - 60 if durations[3] else 30,
                            "duration": 20
                        },
                        {
                            "type": "image",
                            "src": "stock://flowchart_branch?theme=programming",
                            "x": 1280,
                            "y": 360,
                            "width": 400,
                            "height": 300,
                            "animation": "fadeIn",
                            "animation_duration": 2,
                            "start_time": durations[3] - 40 if durations[3] else 50,
                            "duration": 20
                        },
                        {
                            "type": "text",
                            "content": "Алгоритмы строятся из следования, ветвления и цикла. Следование — шаги один за другим. Ветвление — выбор по условию. Цикл — повторение.",
                            "x": 100,
                            "y": 900,
                            "width": 1720,
                            "font": "Arial",
                            "font_size": 40,
                            "color": "#FFFFFF",
                            "background_color": "rgba(0,0,0,0.7)",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 1,
                            "start_time": 2,
                            "duration": durations[3] - 2 if durations[3] else 88
                        },
                        {
                            "type": "audio",
                            "src": "file://C:/Videos/Audio/scene4.mp3",
                            "start_time": 0,
                            "volume": 1.0
                        }
                    ]
                },
                {
                    "id": "conclusion",
                    "duration": durations[4] if durations[4] else 60,
                    "elements": [
                        {
                            "type": "video",
                            "src": "stock://engineer?theme=tech",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "animation": "fadeIn",
                            "animation_duration": 2
                        },
                        {
                            "type": "text",
                            "content": "Программирование — это умение разбивать задачи на шаги. Для электроэнергетиков оно помогает автоматизировать процессы. До встречи на следующем уроке!",
                            "x": 100,
                            "y": 900,
                            "width": 1720,
                            "font": "Arial",
                            "font_size": 40,
                            "color": "#FFFFFF",
                            "background_color": "rgba(0,0,0,0.7)",
                            "align": "center",
                            "animation": "fadeIn",
                            "animation_duration": 1,
                            "start_time": 2,
                            "duration": durations[4] - 2 if durations[4] else 58
                        },
                        {
                            "type": "audio",
                            "src": "file://C:/Videos/Audio/scene5.mp3",
                            "start_time": 0,
                            "volume": 1.0
                        }
                    ]
                }
            ],
            "settings": {
                "language": "ru"
            }
        }
    }

# Загрузка аудио
def upload_audio_to_json2video(audio_path):
    try:
        with open(audio_path, 'rb') as f:
            headers = {"Authorization": f"Bearer {JSON2VIDEO_API_KEY}"}
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            response = requests.post("https://api.json2video.com/v1/files", headers=headers, files=files, timeout=30)
            response.raise_for_status()
            file_url = response.json().get("url")
            logger.info(f"Загружен файл {audio_path}: {file_url}")
            return file_url
    except Exception as e:
        logger.error(f"Ошибка загрузки {audio_path}: {e}")
        return None

# Отправка запроса
def create_video_with_json2video():
    json_payload = get_video_json()
    audio_files = [
        "C:/Videos/Audio/scene1.mp3",
        "C:/Videos/Audio/scene2.mp3",
        "C:/Videos/Audio/scene3.mp3",
        "C:/Videos/Audio/scene4.mp3",
        "C:/Videos/Audio/scene5.mp3"
    ]

    # Загружаем аудио
    audio_urls = []
    for audio_path in audio_files:
        url = upload_audio_to_json2video(audio_path)
        if url:
            audio_urls.append(url)
        else:
            logger.error(f"Не удалось загрузить {audio_path}")
            return None

    # Обновляем JSON
    for i, scene in enumerate(json_payload["project"]["scenes"]):
        for element in scene["elements"]:
            if element.get("type") == "audio":
                element["src"] = audio_urls[i]

    headers = {
        "Authorization": f"Bearer {JSON2VIDEO_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        logger.info("Отправка запроса в JSON2Video")
        response = requests.post("https://api.json2video.com/v1/videos", headers=headers, json=json_payload, timeout=150)
        response.raise_for_status()
        job_id = response.json().get("job_id")
        logger.info("JSON2Video задача запущена: %s", job_id)
        return job_id
    except Exception as e:
        logger.error("Ошибка JSON2Video: %s", str(e))
        return None

# Проверка статуса
def check_video_status(job_id):
    headers = {"Authorization": f"Bearer {JSON2VIDEO_API_KEY}"}
    try:
        response = requests.get(f"https://api.json2video.com/v1/videos/{job_id}", headers=headers, timeout=30)
        response.raise_for_status()
        status_data = response.json()
        logger.info("Статус видео: %s", status_data.get("status"))
        return status_data
    except Exception as e:
        logger.error("Ошибка проверки статуса: %s", str(e))
        return None

# Скачивание видео
def download_video(video_url, output_path):
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("Видео сохранено в %s", output_path)
        return True
    except Exception as e:
        logger.error("Ошибка скачивания: %s", str(e))
        return False

# Django View
@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):
    def get(self, request, *args, **kwargs):
        return self.create_video()

    def post(self, request, *args, **kwargs):
        return self.create_video()

    def create_video(self):
        try:
            logger.info("Начало создания видео")
            job_id = create_video_with_json2video()
            if not job_id:
                logger.error("Не удалось запустить рендеринг")
                return JsonResponse({'error': 'Failed to start video rendering'}, status=500)

            video_url = None
            for _ in range(30):
                status = check_video_status(job_id)
                if status and status.get("status") == "completed":
                    video_url = status.get("video_url")
                    break
                time.sleep(10)

            if not video_url:
                logger.error("Превышено время ожидания рендеринга")
                return JsonResponse({'error': 'Video rendering timeout'}, status=500)

            output_video = os.path.join(OUTPUT_DIR, 'lesson_1.mp4')
            if not download_video(video_url, output_video):
                logger.error("Не удалось скачать видео")
                return JsonResponse({'error': 'Failed to download video'}, status=500)

            logger.info("Возвращаем видео: %s", output_video)
            return FileResponse(open(output_video, 'rb'), as_attachment=True, filename='lesson_1.mp4')
        except Exception as e:
            logger.error("Ошибка обработки: %s", str(e))
            return JsonResponse({'error': str(e)}, status=500)