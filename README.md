# Telegram Tarot Bot

Телеграм-бот для гадания на картах Таро с интеграцией OpenAI и платежной системой ЮKassa.

## Локальный запуск

1. Установите зависимости:
```
pip install -r requirements.txt
```

2. Создайте файл `.env` в корне проекта со следующими переменными:
```
BOT_TOKEN=ваш_токен_бота
OPENAI_API_KEY=ваш_ключ_api_openai
YOOKASSA_SHOP_ID=ваш_id_магазина
YOOKASSA_SECRET_KEY=ваш_секретный_ключ
```

3. Запустите бота в режиме long polling:
```
python main.py
```

## Деплой на Render

### Автоматический деплой

1. Загрузите код в GitHub/GitLab репозиторий
2. Зарегистрируйтесь на [Render](https://render.com/)
3. Создайте новый веб-сервис:
   - Выберите "New" → "Web Service"
   - Подключите свой репозиторий
   - Render автоматически обнаружит `render.yaml` и применит настройки

4. Добавьте секретные переменные окружения в настройках сервиса:
   - `BOT_TOKEN` — токен вашего Telegram бота
   - `OPENAI_API_KEY` — ключ API OpenAI
   - `YOOKASSA_SHOP_ID` — ID вашего магазина в ЮKassa
   - `YOOKASSA_SECRET_KEY` — секретный ключ ЮKassa

### Ручной деплой

Если автоматический деплой не сработал:

1. Создайте новый веб-сервис на Render
2. Настройте следующие параметры:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.webhook:app`
   - **Health Check Path**: `/`

3. Добавьте те же переменные окружения, что указаны выше

## Структура проекта

- `api/webhook.py` - FastAPI приложение для обработки вебхуков от Telegram
- `handlers/` - обработчики команд и сообщений бота
- `services/` - сервисы для работы с внешними API
- `main.py` - скрипт для локального запуска бота в режиме long polling
- `Procfile` - конфигурация для запуска на Render
- `render.yaml` - конфигурация для автоматического деплоя на Render