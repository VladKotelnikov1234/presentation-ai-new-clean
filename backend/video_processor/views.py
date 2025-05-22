def process_methodology_text(raw_text, test_mode=True):
    target_words = 75 if test_mode else 250
    lesson_count = 3 if test_mode else 5

    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY не задан")
        return None

    logger.info(f"Используется OPENROUTER_API_KEY: {OPENROUTER_API_KEY[:5]}... (длина: {len(OPENROUTER_API_KEY)})")
    logger.info(f"Длина raw_text: {len(raw_text)} символов")

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

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://service-lessons.onrender.com",
        "X-Title": "VideoLessonService"
    }
    data = {
        "model": "x-ai/grok-3-beta",
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