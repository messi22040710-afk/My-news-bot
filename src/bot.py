import requests  # Убедись, что модуль есть в requirements.txt

# Функция для переписывания новости
def rewrite_news(title, link):
    if not OPENROUTER_API_KEY:  # Если ключа нет, возвращаем как есть
        return f"📰 {title}\n\n🔗 Подробнее: {link}"
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "deepseek/deepseek-r1-0528-qwen3-8b:free", # Бесплатная мощная модель[reference:5]
                "messages": [{"role": "user", "content": f"Перепиши эту новость для Телеграм-канала: {title}. Ссылка: {link}"}],
                "max_tokens": 300,
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        return f"📰 {title}\n\n🔗 Подробнее: {link}"
