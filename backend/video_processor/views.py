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

# Настройка логгера
logger = logging.getLogger(__name__)

# Предполагаемый импорт API-ключей (из settings.py)
from django.conf import settings
OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY
SYNTHESIA_API_KEY = settings.SYNTHESIA_API_KEY

def extract_content_from_pdf(pdf_path, max_pages=3):
    """Извлекает текст из первых max_pages страниц PDF, ограничивая 2000 символов."""
    text_content = []
    exclude_keywords = ["министерство", "университет", "кафедра", "удк", "издательский", "одобрено", "бакалавр", "челябинск"]
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"Всего страниц: {total_pages}")
        for i, page in enumerate(pdf.pages[:max_pages]):
            text = page.extract_text() or ""
            if not any(keyword in text.lower() for keyword in exclude_keywords):
                text_content.append(f"Страница {i+1}:\n{text}")
    
    return "\n".join(text_content)[:2000]  # Ограничиваем 2000 символов

def process_methodology_text(raw_text, test_mode=True):
    """Обрабатывает текст и создаёт один короткий урок."""
    target_words = 75 if test_mode else 250
    lesson_count = 1  # Один урок для короткого видео

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY не задан")
        return None

    logger.info(f"Используется OPENROUTER_API_KEY: {OPENROUTER_API_KEY[:5]}... (длина: {len(OPENROUTER_API_KEY)})")
    logger.info(f"Длина raw_text: {len(raw_text)} символов")

    prompt = (
        "Ты — преподаватель, создающий короткие видеоуроки для любого предмета (физика, химия, программирование и т.д.). "
        "Обработай текст методички (первые 2-3 страницы, около 2000 символов) и сделай следующее:\n"
        "1. Фильтруй текст: оставь только ключевой контент (объяснения, формулы, уравнения, блок-схемы, код), удали титульные страницы, оглавление, информацию о вузе, кафедрах, издательствах.\n"
        "2. Раздели текст на {lesson_count} короткий урок. Ориентируйся на {target_words} слов (±25 слов).\n"
        "3. Начинай урок с 'В этом уроке разберём...' и заканчивай 'К концу урока вы сможете...'.\n"
        "4. Выделяй формулы (например, E=mc²), уравнения (например, H₂O → H₂ + O₂), блок-схемы (описывай текстом, например, 'Блок-схема: шаг 1 -> шаг 2'), код (с отступами) отдельно.\n"
        "5. Адаптируйся к любому предмету: физика (законы, формулы), химия (реакции), программирование (алгоритмы).\n"
        "6. Абзацы разделяй пустой строкой.\n"
        "7. Формат ответа:\n"
        "[Урок 1]\nТекст...\n\n"
        "Текст методички:\n" + raw_text
    ).format(lesson_count=lesson_count, target_words=target_words)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://service-lessons.onrender.com",
        "X-Title": "VideoLessonService"
    }
    data = {
        "model": "google/gemma-3n-e4b-it:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        logger.info(f"Отправка запроса к OpenRouter с prompt длиной: {len(prompt)} символов")
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        logger.info("Запрос успешно выполнен")
        content = response.json()["choices"][0]["message"]["content"]
        lessons = []
        current_lesson = ""
        for line in content.split('\n'):
            if line.startswith('[Урок'):
                if current_lesson:
                    lessons.append(current_lesson.strip())
                current_lesson = line + "\n"
            else:
                current_lesson += line + "\n"
        if current_lesson:
            lessons.append(current_lesson.strip())
        if not lessons:
            logger.warning("Ответ от OpenRouter пуст или не содержит уроков")
        return lessons[:lesson_count]
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка вызова OpenRouter API: {e}, статус код: {getattr(e.response, 'status_code', 'N/A')}, текст: {getattr(e.response, 'text', 'N/A')}")
        return None
    except Exception as e:
        logger.error(f"Неизвестная ошибка в process_methodology_text: {e}")
        return None

def extract_audio_from_video(video_path):
    """Извлекает аудио из видео и ограничивает длительность."""
    output_path = video_path.replace('.mp4', '.mp3').replace('.avi', '.mp3')
    video = VideoFileClip(video_path)
    if video.duration > 30:  # Ограничиваем 30 секунд
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
            # Здесь нужна реализация загрузки файлов по URL (например, с requests)
            # Для примера оставим заглушку
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

            audio_path = None
            if video_path and video_file.name.endswith(('.mp4', '.avi')):
                audio_path = extract_audio_from_video(video_path)
                if not audio_path:
                    return JsonResponse({'error': 'Не удалось извлечь аудио из видео'}, status=500)
            elif video_file and video_file.name.endswith('.mp3'):
                audio_path = video_path

            raw_text = extract_content_from_pdf(pdf_path)
            logger.info(f"Извлечён текст из PDF, длина: {len(raw_text)} символов")
            if not raw_text or len(raw_text.strip()) == 0:
                return JsonResponse({'error': 'Текст из PDF пуст или не извлечён'}, status=500)

            lessons = process_methodology_text(raw_text, test_mode)
            if not lessons:
                return JsonResponse({'error': 'Не удалось обработать текст в уроки (OpenRouter API ошибка)'}, status=500)

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