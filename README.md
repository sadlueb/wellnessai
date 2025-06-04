# Wellness AI Telegram Bot

Пример минимального бота на `python-telegram-bot` для сбора данных пользователя и получения рекомендаций через Make.com.

## Запуск
1. Установите зависимости:
   ```bash
   pip install python-telegram-bot==13.15 requests
   ```
2. Задайте переменные окружения:
   - `TELEGRAM_TOKEN` — токен вашего бота
   - `MAKE_WEBHOOK_URL` — webhook Make для отправки профиля и получения рекомендаций
   - `MAKE_ACTION_WEBHOOK_URL` — webhook Make для логирования действий пользователя

3. Запустите скрипт:
   ```bash
   python bot.py
   ```

## Пример Make-сценария
Файл [`ProfileToRecommendation.json`](ProfileToRecommendation.json) содержит простую схему:
- `custom_webhook` принимает данные профиля
- модуль OpenAI генерирует текст рекомендаций
- ответ возвращается в HTTP Response в формате:
  ```json
  {"recommendation": "текст"}
  ```

## Пример prompt для OpenAI
```
Ты — wellness‑ассистент. Пользователь: пол {{gender}}, эмоция {{emotion}}, цель {{goal}}.
Сформулируй короткий список советов (2–3 пункта), который поможет достичь цели. Текст не более 500 символов.
```

## Карточка с рекомендацией
Текст отправляется в Markdown и сопровождается инлайн‑кнопками:
```python
keyboard = [
    [
        InlineKeyboardButton("❤️ Нравится", callback_data="like"),
        InlineKeyboardButton("🔁 Ещё одну", callback_data="more"),
        InlineKeyboardButton("💾 Сохранить", callback_data="save"),
    ]
]
update.message.reply_markdown_v2(recommendation_text, reply_markup=InlineKeyboardMarkup(keyboard))
```
Нажатия на кнопки отправляются во второй webhook.
