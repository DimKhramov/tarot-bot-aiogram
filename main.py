import asyncio
import logging
import sys
from os import getenv

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, '.')

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Импортируем роутеры обработчиков
from handlers.tarot_handlers import router as tarot_router
from handlers.payment_handlers import router as payment_router

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
from aiogram.client.default import DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Регистрация обработчиков
dp.include_router(tarot_router)
dp.include_router(payment_router)

async def main():
    """Запуск бота в режиме long polling."""
    # Удаляем вебхук перед запуском long polling
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен в режиме long polling")
    logging.info(f"Имя бота: {(await bot.get_me()).username}")
    print("Бот успешно запущен! Отправьте команду /start в Telegram.")
    
    # Запускаем long polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")