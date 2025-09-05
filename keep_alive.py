from flask import Flask
from threading import Thread
import logging
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем Flask приложение
app = Flask('')

@app.route('/')
def home():
    """Простой эндпоинт для проверки работоспособности."""
    return "Tarot Bot is running!"

@app.route('/ping')
def ping():
    """Эндпоинт для пинга от внешних сервисов."""
    return "pong"

def run():
    """Запускает Flask сервер на порту 8080."""
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Запускает Flask сервер в отдельном потоке."""
    logging.info("Запуск сервера для поддержания работы бота")
    server = Thread(target=run)
    server.daemon = True
    server.start()
    
    # Получаем URL для пинга
    repl_owner = os.getenv("REPL_OWNER")
    repl_slug = os.getenv("REPL_SLUG")
    
    if repl_owner and repl_slug:
        ping_url = f"https://{repl_slug}.{repl_owner}.repl.co/ping"
        logging.info(f"Для поддержания бота в рабочем состоянии настройте пинг на URL: {ping_url}")
        print(f"\n🔔 Для поддержания бота в рабочем состоянии настройте пинг на URL:\n{ping_url}")