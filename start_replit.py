import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Загружаем переменные окружения
load_dotenv()

# Определяем режим запуска (long polling или webhook)
def determine_run_mode():
    """Определяет режим запуска бота на Replit."""
    # Проверяем наличие переменных окружения Replit
    repl_owner = os.getenv("REPL_OWNER")
    repl_slug = os.getenv("REPL_SLUG")
    
    if repl_owner and repl_slug:
        # Формируем URL для вебхука
        replit_url = f"https://{repl_slug}.{repl_owner}.repl.co"
        os.environ["REPLIT_URL"] = replit_url
        logging.info(f"Обнаружена среда Replit. URL: {replit_url}")
        
        # Проверяем, хочет ли пользователь использовать long polling
        force_polling = os.getenv("FORCE_POLLING", "false").lower() == "true"
        
        if force_polling:
            logging.info("Принудительно используется режим long polling")
            return "polling"
        else:
            logging.info("Используется режим webhook")
            return "webhook"
    else:
        logging.info("Не обнаружена среда Replit или отсутствуют необходимые переменные")
        logging.info("Используется режим long polling")
        return "polling"

async def main():
    """Основная функция запуска бота."""
    # Запускаем сервер для поддержания работы бота
    keep_alive()
    
    # Проверяем токен бота
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("Не указан BOT_TOKEN в переменных окружения")
        print("\nОШИБКА: Не указан BOT_TOKEN!")
        print("Добавьте BOT_TOKEN в Secrets (раздел 🔒) на Replit")
        sys.exit(1)
    
    # Определяем режим запуска
    mode = determine_run_mode()
    
    if mode == "webhook":
        # Импортируем и запускаем вебхук
        try:
            from api.webhook import start_webhook
            await start_webhook()
        except Exception as e:
            logging.error(f"Ошибка при запуске webhook: {e}")
            logging.info("Переключение на режим long polling")
            from main import main as start_polling
            await start_polling()
    else:
        # Запускаем в режиме long polling
        from main import main as start_polling
        await start_polling()

if __name__ == "__main__":
    try:
        # Запускаем бота
        print("\n🤖 Запуск Tarot Bot на Replit...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
        print("\n👋 Бот остановлен")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)