import os
import json
import datetime
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Conversation states
GENDER, EMOTION, GOAL, WAIT_HEALTH, READY = range(5)

TOKEN = os.getenv("TELEGRAM_TOKEN")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")  # webhook for profile -> recommendation
MAKE_ACTION_WEBHOOK_URL = os.getenv("MAKE_ACTION_WEBHOOK_URL")  # webhook for feedback

if not TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN env var is required")


def start(update: Update, context: CallbackContext) -> int:
    keyboard = [["Начать профайлинг"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text("Привет! Я wellness-бот. Нажми кнопку, чтобы начать профайлинг.", reply_markup=reply_markup)
    return GENDER


def gender(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text != "Начать профайлинг":
        context.user_data["gender"] = text
        # ask for emotion
        keyboard = [["Спокойствие", "Тревожность"], ["Радость", "Усталость"]]
        update.message.reply_text("Какое у вас сейчас настроение?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return EMOTION
    else:
        keyboard = [["Мужской", "Женский"]]
        update.message.reply_text("Укажите ваш пол", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
        return GENDER


def emotion(update: Update, context: CallbackContext) -> int:
    context.user_data["emotion"] = update.message.text
    keyboard = [["Расслабление", "Энергия"], ["Фокус"]]
    update.message.reply_text("Какова ваша текущая цель?", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return GOAL


def goal(update: Update, context: CallbackContext) -> int:
    context.user_data["goal"] = update.message.text
    keyboard = [["Подключить Apple Health / Google Fit"], ["Получить рекомендации"]]
    update.message.reply_text("Можешь символически подключить Apple Health или Google Fit", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return WAIT_HEALTH


def wait_health(update: Update, context: CallbackContext) -> int:
    if update.message.text.startswith("Подключить"):
        update.message.reply_text("Готово! Данные подключены.")
        return WAIT_HEALTH
    else:
        return send_profile(update, context)


def send_profile(update: Update, context: CallbackContext) -> int:
    profile = {
        "userId": update.effective_user.id,
        "gender": context.user_data.get("gender"),
        "emotion": context.user_data.get("emotion"),
        "goal": context.user_data.get("goal"),
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=profile)
        data = r.json()
        recommendation = data.get("recommendation", "Не удалось получить рекомендации")
    except Exception:
        recommendation = "Ошибка получения рекомендаций"

    send_recommendation(update, context, recommendation)
    return READY


def send_recommendation(update: Update, context: CallbackContext, text: str):
    keyboard = [
        [
            InlineKeyboardButton("❤️ Нравится", callback_data="like"),
            InlineKeyboardButton("🔁 Ещё одну", callback_data="more"),
            InlineKeyboardButton("💾 Сохранить", callback_data="save"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_markdown_v2(text, reply_markup=markup)


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    action = query.data
    payload = {
        "userId": query.from_user.id,
        "action": action,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    try:
        requests.post(MAKE_ACTION_WEBHOOK_URL, json=payload)
    except Exception:
        pass

    if action == "more":
        dummy_update = update.effective_message
        context.user_data["callback_message"] = dummy_update
        profile = {
            "userId": query.from_user.id,
            "gender": context.user_data.get("gender"),
            "emotion": context.user_data.get("emotion"),
            "goal": context.user_data.get("goal"),
            "timestamp": datetime.datetime.utcnow().isoformat(),
        }
        try:
            r = requests.post(MAKE_WEBHOOK_URL, json=profile)
            data = r.json()
            recommendation = data.get("recommendation", "Не удалось получить рекомендации")
        except Exception:
            recommendation = "Ошибка получения рекомендаций"
        query.edit_message_text(recommendation, reply_markup=query.message.reply_markup, parse_mode='MarkdownV2')


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Диалог завершён", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(Filters.text & ~Filters.command, gender)],
            EMOTION: [MessageHandler(Filters.text & ~Filters.command, emotion)],
            GOAL: [MessageHandler(Filters.text & ~Filters.command, goal)],
            WAIT_HEALTH: [MessageHandler(Filters.text & ~Filters.command, wait_health)],
            READY: [MessageHandler(Filters.text & ~Filters.command, send_profile)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
