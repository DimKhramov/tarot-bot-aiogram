import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot_service.log'
)

def start_bot():
    """Запускает бота в режиме long polling (быстрее для локального использования)"""
    try:
        # Путь к директории проекта
        project_dir = Path(__file__).parent
        
        # Запуск бота через main.py (long polling)
        bot_process = subprocess.Popen(
            [sys.executable, os.path.join(project_dir, "main.py")],
            cwd=project_dir
        )
        
        logging.info(f"Бот запущен с PID: {bot_process.pid}")
        return bot_process
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        return None

def main():
    """Основная функция службы"""
    logging.info("Служба бота запущена")
    
    # Запускаем бота
    bot_process = start_bot()
    
    try:
        # Держим процесс активным
        while True:
            # Проверяем, работает ли процесс бота
            if bot_process and bot_process.poll() is not None:
                logging.warning("Бот остановлен, перезапускаем...")
                bot_process = start_bot()
            
            time.sleep(60)  # Проверка каждую минуту
    except KeyboardInterrupt:
        logging.info("Получен сигнал остановки службы")
        if bot_process:
            bot_process.terminate()
            logging.info("Бот остановлен")
    
    logging.info("Служба бота завершена")

if __name__ == "__main__":
    main()