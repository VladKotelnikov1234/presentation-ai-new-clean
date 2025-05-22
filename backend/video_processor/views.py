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
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY
SYNTHESIA_API_KEY = settings.SYNTHESIA_API_KEY
IOINTELLIGENCE_API_KEY = "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjkzNTZlN2NmLTFmNTctNGE2Yi05NjljLTQzZjI3Njg5MzI3MSIsImV4cCI6NDkwMTU0NTE5OH0.adY0csXaEhKDEc14_Ibgoe91gymgDk3YJrRifWMjoikQGzsbM0c0sGAPcZrrMYpTsXzsZm63U-E53Pssz8z-0Q"  # Твой ключ

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

def process_methodology_text(raw_text, test_mode=True):
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
        "model": "meta-llama/Llama-3.3-70B-Instruct",  # Пример модели, проверь доступные через /models
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

def generate_audio_with_elevenlabs(audio_path, lessons, max_duration=30):
    """Генерирует аудио через ElevenLabs с ограничением длительности."""
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    audio_urls = []
    voice_id = "default_voice_id"  # Замени на реальный voice_id
    for lesson in lessons:
        data = {"text": lesson, "voice_id": voice_id, "duration": max_duration}
        response = requests.post("https://api.elevenlabs.io/v1/text-to-speech", headers=headers, json=data)
        if response.status_code == 200:
            audio_urls.append(response.url)
        else:
            logger.error(f"Ошибка ElevenLabs: {response.status_code} - {response.text}")
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
        try:
            pdf_file = request.FILES.get('file')
            video_file = request.FILES.get('video_file')
            if not pdf_file:
                return JsonResponse({'error': 'PDF файл обязателен'}, status=400)
            pdf_path = os.path.join(settings.MEDIA_ROOT, 'uploads', pdf_file.name)
            video_path = os.path.join(settings.MEDIA_ROOT, 'uploads', video_file.name) if video_file else None
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            if video_file:
                with open(video_path, 'wb') as f:
                    for chunk in video_file.chunks():
                        f.write(chunk)
            audio_path = extract_audio_from_video(video_path) if video_path and video_file.name.endswith(('.mp4', '.avi')) else (video_path if video_file and video_file.name.endswith('.mp3') else None)
            raw_text = extract_content_from_pdf(pdf_path)
            logger.info(f"Извлечён текст из PDF, длина: {len(raw_text)} символов")
            if not raw_text or len(raw_text.strip()) == 0:
                return JsonResponse({'error': 'Текст из PDF пуст или не извлечён'}, status=500)
            lessons = process_methodology_text(raw_text, test_mode)
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