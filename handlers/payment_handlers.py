from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.payment_service import create_invoice, process_successful_payment

# Создаем роутер для обработки платежей
router = Router()

# Обработчик предварительной проверки платежа
@router.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Обработчик предварительной проверки платежа
    Telegram требует ответить на pre_checkout_query
    """
    await pre_checkout_query.answer(ok=True)

# Обработчик успешного платежа
@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """
    Обработчик успешного платежа
    """
    payment = message.successful_payment
    
    # Отправляем подтверждение об успешной оплате
    await message.answer(
        f"✅ *Оплата успешно получена!*\n\n"
        f"Сумма: {payment.total_amount / 100} Stars\n"
        f"ID платежа: {payment.telegram_payment_charge_id[:10]}...\n\n"
        f"Начинаю подготовку вашего гадания...",
        parse_mode="Markdown"
    )
    
    # Обрабатываем успешный платеж
    await process_successful_payment(
        message, 
        payment.total_amount, 
        payment.invoice_payload,
        payment.telegram_payment_charge_id
    )
    
    # Показываем анимацию и генерируем гадание
    from handlers.tarot_handlers import show_tarot_animation, generate_tarot_reading
    
    # Показываем анимацию перед выдачей расклада
    await show_tarot_animation(message)
    
    # Генерируем гадание
    reading = generate_tarot_reading()
    
    # Отправляем результаты гадания
    await message.answer('🔮 *Ваше гадание готово!* 🍸\n\nСпасибо за использование нашего сервиса!', parse_mode="Markdown")
    
    # Отправляем каждую карту с интерпретацией
    for card in reading['cards']:
        await message.answer(
            f"🃏 *{card['name']}*\n\n"
            f"{card['description']}\n\n"
            f"🍸 *Алкогольная интерпретация:*\n{card['drunk_interpretation']}",
            parse_mode="Markdown"
        )
    
    # Отправляем общее толкование
    await message.answer(
        f"🔮 *Общее толкование:*\n\n{reading['summary']}\n\n"
        f"🍸 *Рекомендуемый напиток:*\n"
        f"{reading['recommended_drink']}",
        parse_mode="Markdown"
    )