import os
import logging
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import requests
import pdfplumber
from moviepy.editor import VideoFileClip
import zipfile

logger = logging.getLogger(__name__)
from django.conf import settings

# Получение ключей из переменных окружения с проверкой
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
if not ELEVENLABS_API_KEY:
    logger.error("ELEVENLABS_API_KEY не задан")
    raise ValueError("Отсутствует API ключ для ElevenLabs")
SYNTHESIA_API_KEY = os.getenv("SYNTHESIA_API_KEY", "")
if not SYNTHESIA_API_KEY:
    logger.error("SYNTHESIA_API_KEY не задан")
    raise ValueError("Отсутствует API ключ для Synthesia")
IOINTELLIGENCE_API_KEY = os.getenv("IOINTELLIGENCE_API_KEY", "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjkzNTZlN2NmLTFmNTctNGE2Yi05NjljLTQzZjI3Njg5MzI3MSIsImV4cCI6NDkwMTU0NTE5OH0.adY0csXaEhKDEc14_Ibgoe91gymgDk3YJrRifWMjoikQGzsbM0c0sGAPcZrrMYpTsXzsZm63U-E53Pssz8z-0Q")
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
    """Обрабатывает текст и создаёт один короткий урок с помощью IO Intelligence API."""
    target_words = 75
    lesson_count = 1
    prompt = (
        "Ты — преподаватель. Обрабатай текст методички (2000 символов) и создай 1 урок (75 слов): "
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

def extract_audio_from_video(video_path):
    """Извлекает аудио из видео и ограничивает длительность."""
    output_path = video_path.replace('.mp4', '.mp3').replace('.avi', '.mp3')
    video = VideoFileClip(video_path)
    if video.duration > 30:
        video = video.subclip(0, 30)
    video.audio.write_audiofile(output_path, codec='mp3')
    video.close()
    return output_path

def create_custom_voice(audio_path):
    """Создаёт кастомный голос через ElevenLabs."""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    with open(audio_path, "rb") as audio_file:
        files = {
            "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
        }
        data = {
            "name": f"CustomVoice_{os.path.basename(audio_path)}",
            "description": "Голос пользователя из загруженного аудио",
            "labels": {"user_generated": "true"}
        }
        try:
            response = requests.post(
                "https://api.elevenlabs.io/v1/voices/add",
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            response.raise_for_status()
            voice_id = response.json()["voice_id"]
            logger.info(f"Создан кастомный голос с ID: {voice_id}")
            return voice_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка создания голоса: {e.response.status_code if e.response else 'N/A'} - {e.response.text if e.response else str(e)}")
            return None

def generate_audio_with_elevenlabs(audio_path, lessons, max_duration=30):
    """Генерирует аудио через ElevenLabs с кастомным голосом."""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg"
    }
    audio_urls = []
    # Создаём кастомный голос из загруженного аудио
    voice_id = create_custom_voice(audio_path)
    if not voice_id:
        logger.error("Не удалось создать кастомный голос")
        return None, None
    for lesson in lessons:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        data = {
            "text": lesson,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            if response.status_code == 200:
                audio_file_path = os.path.join(settings.MEDIA_ROOT, 'audio', f"lesson_{len(audio_urls)}.mp3")
                os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
                with open(audio_file_path, 'wb') as f:
                    f.write(response.content)
                audio_url = f"/media/audio/lesson_{len(audio_urls)}.mp3"
                audio_urls.append(audio_url)
            else:
                logger.error(f"Ошибка ElevenLabs: {response.status_code} - {response.text}")
                return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к ElevenLabs: {e}")
            return None, None
    return voice_id, audio_urls

def create_video_with_synthesia(lessons, audio_urls, max_duration=30):
    """Создаёт видео через Synthesia с ограничением длительности."""
    headers = {"X-API-Key": SYNTHESIA_API_KEY}
    video_urls = []
    for lesson, audio_url in zip(lessons, audio_urls):
        data = {"script": lesson, "audio_url": audio_url, "duration": max_duration}
        response = requests.post("https://api.synthesia.io/v2/videos", headers=headers, json=data)
        if response.status_code == 200:
            video_urls.append(response.json()["video_url"])
        else:
            logger.error(f"Ошибка Synthesia: {response.status_code} - {response.text}")
            return None
    return video_urls

def create_zip_archive(video_urls):
    """Создаёт ZIP-архив с видео."""
    zip_path = os.path.join(settings.MEDIA_ROOT, 'outputs', 'lessons.zip')
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for url in video_urls:
            # Заглушка: нужно реализовать загрузку файлов по URL
            pass
    return zip_path

@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):
    def post(self, request, *args, **kwargs):
        test_mode = True
        model = request.POST.get('model', 'meta-llama/Llama-3.3-70B-Instruct')  # Добавлен параметр модели
        try:
            pdf_file = request.FILES.get('file')
            video_file = request.FILES.get('video_file')
            if not pdf_file or not video_file:
                return JsonResponse({'error': 'PDF и видео/аудио файлы обязательны'}, status=400)
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'uploads', pdf_file.name)
            video_path = os.path.join(settings.MEDIA_ROOT, 'uploads', video_file.name)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            with open(video_path, 'wb') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)
            audio_path = extract_audio_from_video(video_path) if video_file.name.endswith(('.mp4', '.avi')) else video_path
            raw_text = extract_content_from_pdf(pdf_path)
            logger.info(f"Извлечён текст из PDF, длина: {len(raw_text)} символов")
            if not raw_text or len(raw_text.strip()) == 0:
                return JsonResponse({'error': 'Текст из PDF пуст или не извлечён'}, status=500)
            lessons = process_methodology_text(raw_text, test_mode, model=model)
            if not lessons:
                return JsonResponse({'error': 'Не удалось обработать текст в уроки'}, status=500)
            voice_id, audio_urls = generate_audio_with_elevenlabs(audio_path, lessons, max_duration=30)
            if not audio_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать аудио через ElevenLabs'}, status=500)
            video_urls = create_video_with_synthesia(lessons, audio_urls, max_duration=30)
            if not video_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать видео через Synthesia'}, status=500)
            zip_path = create_zip_archive(video_urls)
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