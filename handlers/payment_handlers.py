from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import re

from services.payment_service import create_invoice, process_successful_payment

# Определяем состояния для FSM
class PaymentStates(StatesGroup):
    waiting_for_birthdate = State()

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
async def successful_payment_handler(message: Message, state: FSMContext):
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
    
    # Импортируем функцию для показа премиум-гадания с анимацией
    from handlers.tarot_handlers import show_premium_reading_with_animation
    
    # Получаем данные пользователя из состояния
    user_data = await state.get_data()
    
    # Получаем дату рождения из состояния пользователя
    birthdate = user_data.get('birthdate', None)
    
    # Если дата рождения не найдена, запрашиваем её у пользователя
    if not birthdate:
        await message.answer(
            "<b>🔮 Для индивидуального гадания мне нужна ваша дата рождения.</b>\n\n"
            "Пожалуйста, введите дату рождения в формате ДД.ММ.ГГГГ (например, 01.01.1990)",
            parse_mode="HTML"
        )
        
        # Устанавливаем состояние ожидания даты рождения
        await state.set_state(PaymentStates.waiting_for_birthdate)
        return
    
    # Показываем премиум-гадание с анимацией и датой рождения
    await show_premium_reading_with_animation(message, birthdate)

# Обработчик ввода даты рождения после оплаты
@router.message(StateFilter(PaymentStates.waiting_for_birthdate))
async def process_birthdate_after_payment(message: Message, state: FSMContext):
    """
    Обработчик ввода даты рождения после оплаты
    """
    # Проверяем формат даты рождения
    birthdate = message.text.strip()
    
    # Проверяем формат даты с помощью регулярного выражения (ДД.ММ.ГГГГ)
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', birthdate):
        await message.answer(
            "<b>❌ Неверный формат даты.</b>\n\n"
            "Пожалуйста, введите дату рождения в формате ДД.ММ.ГГГГ (например, 01.01.1990)",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем дату рождения в состоянии
    await state.update_data(birthdate=birthdate)
    
    # Сбрасываем состояние
    await state.clear()
    
    # Отправляем сообщение о начале гадания
    await message.answer(
        "<b>✅ Дата рождения принята!</b>\n\n"
        "Начинаю подготовку индивидуального гадания с учетом вашей даты рождения...",
        parse_mode="HTML"
    )
    
    # Показываем премиум-гадание с анимацией и датой рождения
    await show_premium_reading_with_animation(message, birthdate)

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
    
    # Добавляем кнопки для нового расклада и возврата назад
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔮 Сделать новый расклад", callback_data="start_reading")
    builder.button(text="🏠 Вернуться в меню", callback_data="return_to_menu")
    builder.adjust(1)  # Размещаем кнопки в один столбец
    
    await message.answer(
        "Хотите сделать новый расклад или вернуться в главное меню?",
        reply_markup=builder.as_markup()
    )