from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Presentation AI",
    },
    extra_body={},
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {
            "role": "user",
            "content": "Проанализируй текст: 'Методичка по программированию: Основы Python. Python - язык с простым синтаксисом. Переменные создаются без объявления типа. Циклы for и while используются для итераций.' Выдели ключевые моменты."
        }
    ]
)

print(completion.choices[0].message.content)