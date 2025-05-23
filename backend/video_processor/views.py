import os
import logging
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import pdfplumber
import zipfile
import time

logger = logging.getLogger(__name__)
from django.conf import settings

# Получение ключей из переменных окружения с проверкой
SYNTHESIA_API_KEY = os.getenv("SYNTHESIA_API_KEY", "").strip()
if not SYNTHESIA_API_KEY:
    logger.error("SYNTHESIA_API_KEY не задан")
    raise ValueError("Отсутствует API ключ для Synthesia")
IOINTELLIGENCE_API_KEY = os.getenv("IOINTELLIGENCE_API_KEY", "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjkzNTZlN2NmLTFmNTctNGE2Yi05NjljLTQzZjI3Njg5MzI3MSIsImV4cCI6NDkwMTU0NTE5OH0.adY0csXaEhKDEc14_Ibgoe91gymgDk3YJrRifWMjoikQGzsbM0c0sGAPcZrrMYpTsXzsZm63U-E53Pssz8z-0Q").strip()
if not IOINTELLIGENCE_API_KEY:
    logger.error("IOINTELLIGENCE_API_KEY не задан")
    raise ValueError("Отсутствует API ключ для IO Intelligence")

def extract_content_from_pdf(pdf_path, max_pages=3):
    """Извлекает текст из первых max_pages страниц PDF, ограничивая 2000 символов."""
    text_content = []
    exclude_keywords = ["министерство", "университет", "кафедра", "удк", "издательский", "одобрено", "бакалавр", "челябинск"]
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            text = page.extract_text() or ""
            if not any(keyword in text.lower() for keyword in exclude_keywords):
                text_content.append(f"Страница {i+1}:\n{text}")
    return "\n".join(text_content)[:2000]

def process_methodology_text(raw_text, test_mode=True, model="meta-llama/Llama-3.3-70B-Instruct"):
    """Обрабатывает текст и создаёт один короткий урок (1 минута, ~120 слов) с помощью IO Intelligence API."""
    target_words = 120  # ~1 минута при скорости 120-150 слов/мин
    lesson_count = 1
    prompt = (
        "Ты — преподаватель. Обрабатай текст методички (2000 символов) и создай 1 урок (120 слов): "
        "1. Фильтруй: оставь объяснения, формулы (E=mc²), уравнения (H₂O → H₂ + O₂), код.\n"
        "2. Начни с 'В этом уроке разберём...' и закончи 'К концу урока вы сможете...'.\n"
        "3. Абзацы разделяй пустой строкой.\n"
        "Текст: " + raw_text
    )
    headers = {
        "Authorization": f"Bearer {IOINTELLIGENCE_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    try:
        response = requests.post(
            "https://api.intelligence.io.solutions/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        lesson = response.json()["choices"][0]["message"]["content"]
        return [lesson]
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка IO Intelligence API: {e.response.status_code if e.response else 'N/A'} - {e.response.text if e.response else str(e)}")
        return None

def create_video_with_synthesia(lessons, max_duration=60):
    """Создаёт тестовое видео через Synthesia без аватара с русским голосом (или без озвучки, если голос недоступен)."""
    headers = {
        "Authorization": f"Bearer {SYNTHESIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    logger.info(f"Формируемый заголовок Authorization: {headers['Authorization']}")
    video_urls = []
    # Пробуем русский голос (замените после проверки доступных голосов)
    available_voices = ["ru-RU-male-1"]
    fallback_voice = None

    for lesson in lessons:
        payload = {
            "title": "Generated Video Lesson",
            "description": "A short test video lesson",
            "visibility": "private",
            "test": True,
            "aspectRatio": "16:9",
            "input": [
                {
                    "scriptText": lesson,
                    "avatar": "",
                    "voice": available_voices[0] if available_voices else fallback_voice,
                    "background": "default"
                }
            ]
        }
        logger.info(f"Отправка запроса к Synthesia API: {payload}")
        try:
            response = requests.post(
                "https://api.synthesia.io/v2/videos",
                headers=headers,
                json=payload,
                timeout=60
            )
            logger.info(f"Ответ от Synthesia: {response.status_code} - {response.text}")
            if response.status_code == 201:
                video_data = response.json()
                video_id = video_data.get("id")
                logger.info(f"Видео создано с ID: {video_id}")
                for _ in range(10):
                    status_response = requests.get(
                        f"https://api.synthesia.io/v2/videos/{video_id}",
                        headers=headers,
                        timeout=30
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "complete":
                            video_url = status_data.get("downloadUrl")
                            if video_url:
                                video_urls.append(video_url)
                                logger.info(f"Видео готово: {video_url}")
                                break
                    time.sleep(30)
                else:
                    logger.error("Видео не было готово после 5 минут ожидания")
                    return None
            else:
                logger.error(f"Ошибка Synthesia: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Synthesia: {e}")
            return None
    return video_urls

def create_zip_archive(video_urls):
    """Создаёт ZIP-архив с видео, загружая их по URL."""
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
        test_mode = True
        model = request.POST.get('model', 'meta-llama/Llama-3.3-70B-Instruct')
        try:
            pdf_file = request.FILES.get('file')
            if not pdf_file:
                return JsonResponse({'error': 'PDF файл обязателен'}, status=400)
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'uploads', pdf_file.name)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            raw_text = extract_content_from_pdf(pdf_path)
            logger.info(f"Извлечён текст из PDF, длина: {len(raw_text)} символов")
            if not raw_text or len(raw_text.strip()) == 0:
                return JsonResponse({'error': 'Текст из PDF пуст или не извлечён'}, status=500)
            lessons = process_methodology_text(raw_text, test_mode, model=model)
            if not lessons:
                return JsonResponse({'error': 'Не удалось обработать текст в уроки'}, status=500)
            video_urls = create_video_with_synthesia(lessons, max_duration=60)
            if not video_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать видео через Synthesia'}, status=500)
            zip_path = create_zip_archive(video_urls)
            if not zip_path:
                return JsonResponse({'error': 'Не удалось создать ZIP архив'}, status=500)
            archive_url = f"/media/outputs/lessons.zip"
            return JsonResponse({'archive_url': archive_url})
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            return JsonResponse({'error': str(e)}, status=500)

class ListModelsView(View):
    def get(self, request, *args, **kwargs):
        headers = {
            "Authorization": f"Bearer {IOINTELLIGENCE_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(
                "https://api.intelligence.io.solutions/api/v1/models",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return JsonResponse(response.json())
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка получения списка моделей: {e}")
            return JsonResponse({'error': str(e)}, status=500)