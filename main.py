import asyncio
import logging
import sys
from os import getenv

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, '.')

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем обработчики
from handlers.tarot_handlers import register_tarot_handlers
from handlers.payment_handlers import register_payment_handlers

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Получаем токен бота из переменных окружения
BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Не указан BOT_TOKEN в .env файле")
    sys.exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Регистрация обработчиков
register_tarot_handlers(dp)
register_payment_handlers(dp)

async def main():
    """Запуск бота в режиме long polling."""
    # Удаляем вебхук перед запуском long polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен в режиме long polling")
    
    # Запускаем long polling
    await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")