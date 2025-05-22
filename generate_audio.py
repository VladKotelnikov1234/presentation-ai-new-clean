import cloudscraper
import os
import time

API_KEY = "sk_1a928b668fcdd7667d58bbdfeae0e0b77347f6e863c9775f"  # Твой ключ
VOICE_ID = "58UEEqZkaMEoEiWrAafQ"  # LessonVoice
OUTPUT_DIR = "C:/Videos/Audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scenes = [
    {"text": "Добро пожаловать на наш урок...", "filename": "scene1.mp3"},
    {"text": "Алгоритм — это чёткая последовательность...", "filename": "scene2.mp3"},
    {"text": "Алгоритм — это план, а программа...", "filename": "scene3.mp3"},
    {"text": "Алгоритмы строятся из трёх основ...", "filename": "scene4.mp3"},
    {"text": "Программирование — это умение...", "filename": "scene5.mp3"}
]

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}
data = {
    "text": "",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
}

scraper = cloudscraper.create_scraper()  # Создаём cloudscraper

for scene in scenes:
    data["text"] = scene["text"]
    for attempt in range(3):
        try:
            response = scraper.post(url, json=data, headers=headers, timeout=30)
            if response.status_code == 200:
                with open(os.path.join(OUTPUT_DIR, scene["filename"]), "wb") as f:
                    f.write(response.content)
                print(f"Сохранено: {scene['filename']}")
                break
            else:
                print(f"Попытка {attempt + 1} не удалась для {scene['filename']}: {response.status_code} - {response.text[:100]}")
                time.sleep(2 ** attempt)
        except Exception as e:
            print(f"Ошибка на попытке {attempt + 1} для {scene['filename']}: {e}")
            time.sleep(2 ** attempt)
    else:
        print(f"Не удалось сгенерировать {scene['filename']} после 3 попыток")