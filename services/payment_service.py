from aiogram import Bot
from aiogram.types import Message, LabeledPrice
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем цену гадания из переменных окружения
TAROT_READING_PRICE = int(os.getenv('TAROT_READING_PRICE', 10000))  # 100 Stars = 10000 копеек

async def create_invoice(bot: Bot, chat_id: int, amount: int = None, title: str = "Пьяное Таро - Гадание", description: str = "Гадание на картах Таро с алкогольной интерпретацией"):
    """
    Создает счет для оплаты гадания на Таро
    
    Для Telegram Stars:
    - Валюта должна быть 'XTR'
    - provider_token должен быть пустой строкой
    - Необходим start_parameter
    
    Параметры:
    - amount: сумма в копейках (если None, используется стандартная цена)
    - title: заголовок счета
    - description: описание услуги
    """
    try:
        # Если сумма не указана, используем стандартную
        if amount is None:
            amount = TAROT_READING_PRICE
            
        # Создаем счет
        await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload="tarot_reading",
            provider_token="",  # Пустая строка для Telegram Stars
            currency="XTR",     # XTR - валюта Telegram Stars
            prices=[
                LabeledPrice(
                    label="Гадание на Таро",
                    amount=amount
                )
            ],
            start_parameter="tarot_reading",  # Необходимо для Telegram Stars
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
            protect_content=False
        )
        return True
    except Exception as e:
        print(f"Ошибка при создании счета: {e}")
        return False

async def process_successful_payment(message: Message, amount: int, payload: str, payment_id: str):
    """
    Обрабатывает успешный платеж
    
    Args:
        message: Сообщение с информацией о платеже
        amount: Сумма платежа в копейках
        payload: Полезная нагрузка платежа
        payment_id: ID платежа в Telegram
    """
    # Логируем информацию о платеже
    print(f"Успешный платеж: {amount} копеек, payload: {payload}, ID: {payment_id}")
    
    # Здесь можно добавить сохранение информации о платеже в базу данных
    
    # Отправляем сообщение пользователю
    await message.answer(
        "✅ Оплата успешно получена! Приступаю к гаданию...",
        parse_mode="Markdown"
    )