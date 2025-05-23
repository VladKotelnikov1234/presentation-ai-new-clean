import os
import logging
import socket
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import zipfile
import time

logger = logging.getLogger(__name__)
from django.conf import settings

# API-ключ HeyGen
HEYGEN_API_KEY = "MjIyNTE3MjVhODZhNDM5NGFlOTQzZDEzZDM0ZmVhZjMtMTc0ODAwNDM3NA=="

def check_dns_resolution(hostname, max_attempts=3, delay=10):
    """Проверяет, можно ли разрешить доменное имя."""
    for attempt in range(max_attempts):
        try:
            socket.getaddrinfo(hostname, 443)
            logger.info(f"DNS для {hostname} успешно разрешён")
            return True
        except socket.gaierror as e:
            logger.warning(f"Не удалось разрешить DNS для {hostname}, попытка {attempt + 1}/{max_attempts}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
    return False

def create_video_with_heygen(lessons, max_duration=30, max_retries=3):
    """Создаёт видео через HeyGen (2 видео по 30 секунд)."""
    if not check_dns_resolution("api.heygen.com"):
        logger.error("Не удалось разрешить DNS для api.heygen.com после всех попыток")
        return None

    video_urls = []
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }

    for i, lesson in enumerate(lessons):
        retries = 0
        while retries < max_retries:
            lesson_text = lesson[:1500]  # Ограничение HeyGen
            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": "Daisy-inskirt-20220818",
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "text",
                            "input_text": lesson_text,
                            "voice_id": "2d5b0e6cf36f460aa7fc47e3eee4ba54",
                            "speed": 1.0
                        },
                        "background": {
                            "type": "color",
                            "value": "#008000"
                        }
                    }
                ],
                "dimension": {
                    "width": 1280,
                    "height": 720
                },
                "test": True  # Тестовый режим (с водяным знаком)
            }
            logger.info(f"Попытка {retries + 1}/{max_retries} отправки запроса к HeyGen API для урока {i}: {payload}")
            try:
                response = requests.post(
                    "https://api.heygen.com/v2/video/generate",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                logger.info(f"Ответ от HeyGen: {response.status_code} - {response.text}")
                if response.status_code == 200:
                    video_data = response.json()
                    if "data" not in video_data or "video_id" not in video_data["data"]:
                        logger.error(f"Некорректный ответ от HeyGen: {video_data}")
                        return None
                    video_id = video_data["data"]["video_id"]
                    video_status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"
                    for _ in range(20):
                        status_response = requests.get(
                            video_status_url,
                            headers=headers,
                            timeout=30
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            status = status_data["data"]["status"]
                            if status == "completed":
                                video_url = status_data["data"]["video_url"]
                                if video_url:
                                    video_urls.append(video_url)
                                    logger.info(f"Видео {i} готово: {video_url}")
                                    break
                            elif status == "failed":
                                error = status_data["data"].get("error", "Неизвестная ошибка")
                                logger.error(f"Рендеринг урока {i} завершился с ошибкой: {error}")
                                return None
                            elif status in ["processing", "pending"]:
                                logger.info(f"Видео {i} обрабатывается, ждем...")
                                time.sleep(30)
                        else:
                            logger.error(f"Ошибка проверки статуса: {status_response.status_code} - {status_response.text}")
                            return None
                    else:
                        logger.error(f"Видео {i} не было готово после 10 минут ожидания")
                        return None
                    break
                else:
                    logger.error(f"Ошибка HeyGen для урока {i}: {response.status_code} - {response.text}")
                    retries += 1
                    if retries < max_retries:
                        time.sleep(2 ** retries)
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса к HeyGen для урока {i}: {e}")
                retries += 1
                if retries < max_retries:
                    time.sleep(2 ** retries)
        else:
            logger.error(f"Превышено максимальное количество попыток для урока {i}")
            return None
    return video_urls

def create_zip_archive(video_urls):
    """Создаёт ZIP-архив с видео."""
    zip_path = os.path.join(settings.MEDIA_ROOT, 'outputs', 'lessons.zip')
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i, url in enumerate(video_urls):
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                video_path = os.path.join(settings.MEDIA_ROOT, 'outputs', f"lesson_{i}.mp4")
                with open(video_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                zipf.write(video_path, f"lesson_{i}.mp4")
                os.remove(video_path)
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка загрузки видео по URL {url}: {e}")
                return None
    return zip_path

@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):
    def post(self, request, *args, **kwargs):
        try:
            lessons = [
                "В этом уроке разберём основы. Это пример текста для первого тестового видео на русском языке.",
                "В этом уроке продолжим изучение. Это пример текста для второго тестового видео на русском языке."
            ]
            video_urls = create_video_with_heygen(lessons, max_duration=30)
            if not video_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать видео через HeyGen'}, status=500)
            zip_path = create_zip_archive(video_urls)
            if not zip_path:
                return JsonResponse({'error': 'Не удалось создать ZIP архив'}, status=500)
            archive_url = f"/media/outputs/lessons.zip"
            return JsonResponse({'archive_url': archive_url})
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            return JsonResponse({'error': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ListModelsView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"message": "This endpoint is not implemented yet"}, status=200)