import os
import logging
import time
import requests
import zipfile
import re
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings
import pdfplumber
import moviepy.editor as mp
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

# Настройка логирования
logger = logging.getLogger(__name__)
os.makedirs('media/logs', exist_ok=True)
handler = logging.FileHandler('media/logs/debug_new.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Настройки API и параметров
ELEVENLABS_API_KEY = "sk_1a928b668fcdd7667d58bbdfeae0e0b77347f6e863c9775f"
SYNTHESIA_API_KEY = "399b87cac1835dd1e65602af9fe8a2b3"
OPENROUTER_API_KEY = "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"
OUTPUT_DIR = 'media/outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)
MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', 'media')

# Инициализация OpenAI клиента для OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://your-site.com",
        "X-Title": "VideoLessonService"
    }
)


# Извлечение аудио из видео
def extract_audio_from_video(video_path):
    try:
        audio_path = video_path.rsplit('.', 1)[0] + '.mp3'
        video = mp.VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        logger.info(f"Извлечено аудио из видео: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"Ошибка извлечения аудио из видео {video_path}: {e}")
        return None


# Извлечение текста из PDF
def extract_content_from_pdf(pdf_path):
    text_content = []
    exclude_keywords = ["министерство", "университет", "кафедра", "удк", "издательский", "одобрено", "бакалавр"]

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"Всего страниц: {total_pages}")
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if not any(keyword in text.lower() for keyword in exclude_keywords):
                text_content.append(f"Страница {i + 1}:\n{text}")

    return "\n".join(text_content)


# Обработка методички и разделение на уроки
def process_methodology_text(raw_text, test_mode=True):
    target_words = 75 if test_mode else 250  # 75 слов для 30 сек, 250 для 2 мин
    lesson_count = 3 if test_mode else 5  # 2-3 урока для теста, 5 для продакшена

    prompt = (
            "Ты — преподаватель, создающий видеоуроки для любого предмета (физика, химия, программирование и т.д.). "
            "Обработай текст методички и сделай следующее:\n"
            "1. Фильтруй текст: оставь только ключевой контент (объяснения, формулы, уравнения, блок-схемы, код), удали титульные страницы, оглавление, информацию о вузе, кафедрах, издательствах.\n"
            "2. Раздели текст на {lesson_count} урока по темам. Ориентируйся на {target_words} слов на урок (±25 слов).\n"
            "3. Начинай урок с 'В этом уроке разберём...' и заканчивай 'К концу урока вы сможете...'.\n"
            "4. Выделяй формулы (например, E=mc²), уравнения (например, H₂O → H₂ + O₂), блок-схемы (описывай текстом, например, 'Блок-схема: шаг 1 -> шаг 2'), код (с отступами) отдельно.\n"
            "5. Адаптируйся к любому предмету: физика (законы, формулы), химия (реакции), программирование (алгоритмы).\n"
            "6. Абзацы разделяй пустой строкой.\n"
            "7. Формат ответа:\n"
            "[Урок 1]\nТекст...\n\n[Урок 2]\nТекст...\n\n"
            "Текст методички:\n" + raw_text
    ).format(lesson_count=lesson_count, target_words=target_words)

    response = client.chat.completions.create(
        model="google/gemini-2.5-pro-preview",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
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
    return lessons[:lesson_count]  # Ограничиваем количество уроков


# Клонирование голоса и генерация аудио через ElevenLabs
def generate_audio_with_elevenlabs(audio_path, lessons):
    voice_id = None
    audio_urls = []

    # 1. Клонирование голоса
    if audio_path:
        try:
            url = "https://api.elevenlabs.io/v1/voices/add"
            headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "multipart/form-data"}
            with open(audio_path, 'rb') as audio_file:
                files = {
                    'name': (None, 'LessonVoice'),
                    'files': (os.path.basename(audio_path), audio_file, 'audio/mpeg'),
                    'description': (None, 'Voice for lessons')
                }
                response = requests.post(url, headers=headers, files=files, timeout=30)
                response.raise_for_status()
                voice_id = response.json().get("voice_id")
                logger.info(f"Голос склонирован: voice_id = {voice_id}")
        except Exception as e:
            logger.error(f"Ошибка клонирования голоса через ElevenLabs: {e}")
            return None, None

    # Если голос не склонирован, используем стандартный голос
    if not voice_id:
        voice_id = "pNInz6obpgDQGcFmaJgB"  # Пример стандартного голоса

    # 2. Генерация аудио
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}

    for i, lesson in enumerate(lessons):
        data["text"] = lesson
        audio_path = os.path.join(OUTPUT_DIR, f"lesson{i + 1}.mp3")
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            with open(audio_path, "wb") as f:
                f.write(response.content)
            audio_urls.append(audio_path)
            logger.info(f"Сохранено аудио: {audio_path}")
        except Exception as e:
            logger.error(f"Ошибка генерации аудио для урока {i + 1}: {e}")
            return None, None

    return voice_id, audio_urls


# Генерация видео через Synthesia
def create_video_with_synthesia(lessons, audio_urls):
    video_urls = []
    headers = {"Authorization": f"Bearer {SYNTHESIA_API_KEY}", "Content-Type": "application/json"}

    for i, (lesson_text, audio_path) in enumerate(zip(lessons, audio_urls)):
        try:
            with open(audio_path, 'rb') as f:
                audio_response = requests.post(
                    "https://api.synthesia.io/v2/files",
                    headers={"Authorization": f"Bearer {SYNTHESIA_API_KEY}"},
                    files={"file": (os.path.basename(audio_path), f, "audio/mpeg")},
                    timeout=30
                )
                audio_response.raise_for_status()
                audio_url = audio_response.json().get("url")
                logger.info(f"Аудио для урока {i + 1} загружено в Synthesia: {audio_url}")
        except Exception as e:
            logger.error(f"Ошибка загрузки аудио в Synthesia для урока {i + 1}: {e}")
            return None

        payload = {
            "scriptText": lesson_text,
            "audioUrl": audio_url,
            "avatar": None,
            "background": {"type": "color", "value": "#000000"},
            "resolution": "1920x1080",
            "duration": 30 if test_mode else 120  # 30 сек для теста, 2 мин для продакшена
        }
        try:
            response = requests.post("https://api.synthesia.io/v2/videos", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            video_id = response.json().get("id")
            logger.info(f"Synthesia: Видео {i + 1} отправлено на рендеринг, ID: {video_id}")

            video_url = None
            for _ in range(30):
                status_response = requests.get(f"https://api.synthesia.io/v2/videos/{video_id}", headers=headers,
                                               timeout=30)
                status_response.raise_for_status()
                status = status_response.json().get("status")
                if status == "complete":
                    video_url = status_response.json().get("download")
                    break
                time.sleep(10)

            if not video_url:
                logger.error(f"Превышено время ожидания рендеринга видео {i + 1}")
                return None

            output_video = os.path.join(OUTPUT_DIR, f"lesson_{i + 1}.mp4")
            response = requests.get(video_url, stream=True)
            with open(output_video, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            video_urls.append(output_video)
            logger.info(f"Сохранено видео: {output_video}")
        except Exception as e:
            logger.error(f"Ошибка генерации видео {i + 1} через Synthesia: {e}")
            return None

    return video_urls


# Создание ZIP-архива
def create_zip_archive(video_files):
    zip_path = os.path.join(OUTPUT_DIR, 'lessons.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for video in video_files:
            zipf.write(video, os.path.basename(video))
    logger.info(f"Создан архив: {zip_path}")
    return zip_path


# Django View для загрузки и обработки файлов
@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):
    def post(self, request, *args, **kwargs):
        test_mode = True  # Переключатель для теста (2-3 урока по 30 сек), False для 5 уроков по 2 мин
        try:
            pdf_file = request.FILES.get('pdf_file')
            media_file = request.FILES.get('media_file')

            if not pdf_file:
                return JsonResponse({'error': 'PDF файл обязателен'}, status=400)

            pdf_path = os.path.join(MEDIA_ROOT, 'uploads', pdf_file.name)
            media_path = os.path.join(MEDIA_ROOT, 'uploads', media_file.name) if media_file else None
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            if media_file:
                with open(media_path, 'wb') as f:
                    for chunk in media_file.chunks():
                        f.write(chunk)

            # Извлечение аудио из видео, если загружено видео
            audio_path = None
            if media_path and media_path.endswith(('.mp4', '.avi')):
                audio_path = extract_audio_from_video(media_path)
                if not audio_path:
                    return JsonResponse({'error': 'Не удалось извлечь аудио из видео'}, status=500)
            elif media_file and media_file.name.endswith('.mp3'):
                audio_path = media_path

            raw_text = extract_content_from_pdf(pdf_path)
            if not raw_text:
                return JsonResponse({'error': 'Не удалось извлечь текст из PDF'}, status=500)

            lessons = process_methodology_text(raw_text, test_mode)
            if not lessons:
                return JsonResponse({'error': 'Не удалось обработать текст в уроки'}, status=500)

            voice_id, audio_urls = generate_audio_with_elevenlabs(audio_path, lessons)
            if not audio_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать аудио через ElevenLabs'}, status=500)

            video_urls = create_video_with_synthesia(lessons, audio_urls)
            if not video_urls:
                return JsonResponse({'error': 'Не удалось сгенерировать видео через Synthesia'}, status=500)

            zip_path = create_zip_archive(video_urls)
            archive_url = f"/media/outputs/lessons.zip"

            return JsonResponse({'archive_url': archive_url})
        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            return JsonResponse({'error': str(e)}, status=500)