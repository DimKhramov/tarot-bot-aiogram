import os
import logging
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

# Добавляем родительскую директорию в sys.path для корректного импорта
# Это важно для Render, чтобы он мог найти модули в папке handlers
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from handlers.tarot_handlers import router as tarot_router
from handlers.payment_handlers import router as payment_router

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# --- Переменные ---
# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Render автоматически предоставляет URL в переменной RENDER_EXTERNAL_URL
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER_SERVICE_URL")
# Путь для вебхука. Использование токена в пути повышает безопасность.
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
# Полный URL вебхука
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}" if RENDER_EXTERNAL_URL else None

# --- Проверки ---
if not BOT_TOKEN:
    logging.critical("Ошибка: BOT_TOKEN не найден в переменных окружения!")
    sys.exit("Ошибка: BOT_TOKEN не найден в переменных окружения")
if not RENDER_EXTERNAL_URL:
    logging.warning("URL сервиса Render не найден. Убедитесь, что деплой на Render прошел успешно.")


# --- Инициализация ---
# FastAPI приложение
app = FastAPI()
# Aiogram бот и диспетчер
bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# --- Роутеры ---
dp.include_router(tarot_router)
dp.include_router(payment_router)


# --- Логика вебхука ---
@app.on_event("startup")
async def on_startup():
    """Устанавливает вебхук при старте приложения."""
    # Проверяем, что мы не на локальной машине и URL существует
    if RENDER_EXTERNAL_URL and WEBHOOK_URL:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url != WEBHOOK_URL:
            await bot.set_webhook(url=WEBHOOK_URL)
            logging.info(f"Вебхук установлен на: {WEBHOOK_URL}")
        else:
            logging.info("Вебхук уже установлен.")
    else:
        logging.warning("Не удалось установить вебхук: отсутствует URL сервиса.")

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    """
    Принимает обновления от Telegram, преобразует их
    и передает в диспетчер aiogram.
    """
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)
    return {"ok": True}

@app.on_event("shutdown")
async def on_shutdown():
    """Корректно завершает сессию бота при остановке."""
    await bot.session.close()
    logging.info("Сессия бота закрыта.")

@app.get("/")
def read_root():
    """Корневой эндпоинт для проверки статуса. Render использует его для health checks."""
    return {"status": "ok"}