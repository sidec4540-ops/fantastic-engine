import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Словарь с ответами
RESPONSES = {
    'привет': 'Привет! Как дела? 😊',
    'здравствуй': 'Здравствуйте! Как поживаете? 🌟',
    'хай': 'Хай! Как настроение? 🎉',
    'как дела': 'У меня всё отлично! А у тебя как? 🤗',
    'что делаешь': 'Общаюсь с тобой! А ты? 💬',
    'нормально': 'Это здорово! Рад за тебя! 😄',
    'хорошо': 'Отлично! Так держать! 👍',
    'плохо': 'Ой, сочувствую. Всё наладится! 🤗',
    'спасибо': 'Пожалуйста! Всегда рад помочь! 🙏',
    'пока': 'Пока! Было приятно пообщаться! 👋',
    'досвидания': 'До свидания! Хорошего дня! 🌞'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        'Привет! Я бот-собеседник. Можешь просто поздороваться со мной! 🤖\n'
        'Используй /help чтобы узнать что я умею.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
🤖 *Я умею отвечать на:*

*Приветствия:*
• привет, здравствуй, хай

*Вопросы:*
• как дела, что делаешь

*Настроение:*
• нормально, хорошо, плохо

*Вежливость:*
• спасибо, пока, досвидания

Просто напиши мне сообщение и я отвечу! 💬
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text.lower().strip()
    user_name = update.message.from_user.first_name
    
    logger.info(f"Получено сообщение от {user_name}: {user_message}")
    
    # Проверяем, есть ли ключевое слово в сообщении
    response = None
    for keyword, answer in RESPONSES.items():
        if keyword in user_message:
            response = answer
            break
    
    # Если ключевое слово не найдено
    if response is None:
        response = random.choice([
            "Интересно... Расскажи ещё что-нибудь! 😊",
            "Понятно! А что ещё? 🤔",
            "Здорово! Продолжай в том же духе! 👍",
            "Я тебя слушаю! 👂"
        ])
    
    await update.message.reply_text(response)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик неизвестных команд"""
    await update.message.reply_text(
        "Извините, я не понимаю эту команду. 😕\n"
        "Используйте /help для списка команд."
    )

def main():
    """Запуск бота"""
    # Ваш токен
    TOKEN = "8202165027:AAHGX9KGanwfaATn68xN8wPxdxEA1y1xLl8"
    
    # Создаём приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Добавляем обработчик неизвестных команд
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    # Запускаем бота
    print("🤖 Бот запущен и готов к работе!")
    print(f"🔗 Найдите бота: https://t.me/{(await application.bot.get_me()).username}")
    print("Нажмите Ctrl+C для остановки")
    
    application.run_polling()

if __name__ == '__main__':
    # Добавляем импорт random для случайных ответов
    import random
    main()