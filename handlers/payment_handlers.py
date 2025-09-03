from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import asyncio

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
    
    # Отправляем сообщение о начале гадания
    await message.answer('<b>🔮 Начинаю гадание...</b>', parse_mode="HTML")
    
    # Генерируем гадание
    reading = generate_tarot_reading()
    
    # Задержка перед первой картой
    await asyncio.sleep(2)
    
    # Сообщение о перемешивании карт
    shuffling_msg = await message.answer('<b>🃏 Перемешиваю карты...</b>', parse_mode="HTML")
    
    # Задержка перед первой картой
    await asyncio.sleep(3)
    
    # Показываем первую карту
    await message.answer(
        f"<b>🃏 Первая карта: {reading['cards'][0]['name']}</b>\n\n"
        f"{reading['cards'][0]['description']}\n\n"
        f"<b>🍸 Алкогольная интерпретация:</b>\n{reading['cards'][0]['drunk_interpretation']}",
        parse_mode="HTML"
    )
    
    # Сообщение о перемешивании карт перед второй картой
    await shuffling_msg.edit_text('<b>🃏 Снова перемешиваю карты...</b>', parse_mode="HTML")
    
    # Задержка перед второй картой
    await asyncio.sleep(3)
    
    # Показываем вторую карту
    await message.answer(
        f"<b>🃏 Вторая карта: {reading['cards'][1]['name']}</b>\n\n"
        f"{reading['cards'][1]['description']}\n\n"
        f"<b>🍸 Алкогольная интерпретация:</b>\n{reading['cards'][1]['drunk_interpretation']}",
        parse_mode="HTML"
    )
    
    # Сообщение о перемешивании карт перед третьей картой
    await shuffling_msg.edit_text('<b>🃏 Последний раз перемешиваю карты...</b>', parse_mode="HTML")
    
    # Задержка перед третьей картой
    await asyncio.sleep(3)
    
    # Показываем третью карту
    await message.answer(
        f"<b>🃏 Третья карта: {reading['cards'][2]['name']}</b>\n\n"
        f"{reading['cards'][2]['description']}\n\n"
        f"<b>🍸 Алкогольная интерпретация:</b>\n{reading['cards'][2]['drunk_interpretation']}",
        parse_mode="HTML"
    )
    
    # Сообщение о подготовке вердикта
    await shuffling_msg.edit_text('<b>✨ Поддаюсь небесам и готовлю вердикт...</b>', parse_mode="HTML")
    
    # Задержка перед финальным вердиктом
    await asyncio.sleep(4)
    
    # Отправляем общее толкование
    await message.answer(
        f"<b>🔮 Общее толкование:</b>\n\n{reading['summary']}\n\n"
        f"<b>🍸 Рекомендуемый напиток:</b>\n"
        f"{reading['recommended_drink']}",
        parse_mode="HTML"
    )