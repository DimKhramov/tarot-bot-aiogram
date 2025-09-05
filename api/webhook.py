import os
import logging
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

# Добавляем родительскую директорию в sys.path для корректного импорта
# Это важно для Replit, чтобы он мог найти модули в папке handlers
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logging.info("Запуск приложения webhook.py")

# Загрузка переменных окружения из .env файла (если файл существует)
env_path = os.path.join(parent_dir, '.env')
if os.path.exists(env_path):
    logging.info(f"Загрузка переменных окружения из {env_path}")
    load_dotenv(env_path)
else:
    logging.info("Файл .env не найден, используем переменные окружения из системы")

from handlers.tarot_handlers import router as tarot_router
from handlers.payment_handlers import router as payment_router

# --- Переменные ---
# Токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.info(f"BOT_TOKEN получен: {'Да' if BOT_TOKEN else 'Нет'}")

# Replit URL для вебхука
REPLIT_URL = os.getenv("REPLIT_URL") or os.getenv("REPL_SLUG") and os.getenv("REPL_OWNER") and f"https://{os.getenv('REPL_SLUG')}.{os.getenv('REPL_OWNER')}.repl.co"
logging.info(f"REPLIT_URL: {REPLIT_URL}")

# Путь для вебхука. Использование токена в пути повышает безопасность.
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}" if BOT_TOKEN else "/webhook/default"
logging.info(f"WEBHOOK_PATH: {WEBHOOK_PATH}")

# Полный URL вебхука
WEBHOOK_URL = f"{REPLIT_URL}{WEBHOOK_PATH}" if REPLIT_URL else None
logging.info(f"WEBHOOK_URL: {WEBHOOK_URL}")

# Логирование всех переменных окружения (без значений)
logging.info(f"Доступные переменные окружения: {', '.join([k for k in os.environ.keys()])}")

# --- Проверки ---
if not BOT_TOKEN:
    logging.critical("Ошибка: BOT_TOKEN не найден в переменных окружения!")
    # Не завершаем приложение, чтобы оно могло запуститься на Replit для отладки
    # sys.exit("Ошибка: BOT_TOKEN не найден в переменных окружения")
    logging.warning("Приложение продолжит работу без BOT_TOKEN для отладки")
if not REPLIT_URL:
    logging.warning("URL сервиса Replit не найден. Убедитесь, что переменные REPLIT_URL или REPL_SLUG и REPL_OWNER настроены правильно.")


# --- Инициализация ---
# FastAPI приложение
app = FastAPI()
# Aiogram бот и диспетчер
from aiogram.client.default import DefaultBotProperties
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Роутеры ---
dp.include_router(tarot_router)
dp.include_router(payment_router)


# --- Логика вебхука ---
# Флаг для отслеживания установки вебхука
webhook_set = False

@app.on_event("startup")
async def on_startup():
    """Устанавливает вебхук при старте приложения."""
    global webhook_set
    
    if webhook_set:
        logging.info("Вебхук уже установлен.")
        return
        
    # Проверяем, что мы не на локальной машине и URL существует
    if REPLIT_URL and WEBHOOK_URL:
        try:
            webhook_info = await bot.get_webhook_info()
            if webhook_info.url != WEBHOOK_URL:
                await bot.set_webhook(url=WEBHOOK_URL)
                logging.info(f"Вебхук установлен на: {WEBHOOK_URL}")
            else:
                logging.info("Вебхук уже установлен.")
            webhook_set = True
        except Exception as e:
            logging.error(f"Ошибка при установке вебхука: {e}")
    else:
        logging.warning("Не удалось установить вебхук: отсутствует URL сервиса.")

# Функция для запуска вебхука из start_replit.py
async def start_webhook():
    """Запускает бота в режиме вебхука."""
    logging.info("Запуск бота в режиме вебхука")
    # Вызываем on_startup вручную, так как FastAPI не запускается напрямую
    await on_startup()
    # Запускаем uvicorn сервер
    port = int(os.getenv("PORT", 8080))
    logging.info(f"Запуск uvicorn сервера на порту {port}")
    # Запускаем сервер в неблокирующем режиме
    config = uvicorn.Config("api.webhook:app", host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

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
    """Корневой эндпоинт для проверки статуса. Replit использует его для health checks и пингов."""
    return {"status": "ok"}