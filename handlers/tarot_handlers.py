import json
import asyncio
import random
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from openai import OpenAI
from services.payment_service import create_invoice

# Класс состояний для индивидуального гадания
class PremiumReadingStates(StatesGroup):
    waiting_for_birthdate = State()  # Ожидание ввода даты рождения

# Инициализация клиента OpenAI
client = OpenAI()

# Константы для промптов
PROMPT_TAROT_CARDS = "Сгенерируй 3 уникальные карты Таро с описанием, кратким значением и алкогольной интерпретацией. Верни результат в формате JSON: [{\"id\":..., \"name\":..., \"description\":..., \"short_meaning\":..., \"drunk_interpretation\":...}]"
PROMPT_TAROT_MESSAGE = "Ты - мистический таролог с чувством юмора. Напиши короткое сообщение (до 200 символов) о том, что карты Таро предсказывают для пользователя. Добавь упоминание алкоголя и шуточную рекомендацию."

# Промпт для генерации полного расклада Таро через ChatGPT
PROMPT_TAROT_READING = """Сгенерируй полный расклад Таро из 3 карт с подробным описанием и алкогольной интерпретацией. 
Расклад должен включать:
1. Три уникальные карты Таро с названием, описанием и алкогольной интерпретацией
2. Общее толкование расклада
3. Рекомендуемый алкогольный напиток, соответствующий раскладу

Верни результат в формате JSON:
{
  "cards": [
    {"name": "...", "description": "...", "drunk_interpretation": "..."},
    {"name": "...", "description": "...", "drunk_interpretation": "..."},
    {"name": "...", "description": "...", "drunk_interpretation": "..."}
  ],
  "summary": "...",
  "recommended_drink": "..."
}"""

# Промпт для генерации индивидуального расклада с учетом даты рождения
PROMPT_PREMIUM_READING = """Ты - опытный таролог с алкогольным уклоном. Твоя задача - сделать индивидуальный расклад Таро для человека, родившегося {birthdate}, учитывая текущую дату {current_date}.

Сделай расклад из 5 карт Таро, учитывая астрологические и нумерологические аспекты даты рождения и текущей даты.
Для каждой карты дай название, описание и алкогольную интерпретацию.

Также добавь персональное резюме для человека с этой датой рождения, астрологический комментарий и рекомендацию напитка, который лучше всего подходит этому человеку.

Ответ должен быть в формате JSON:
{
  "cards": [
    {
      "name": "Название карты",
      "description": "Описание карты",
      "drunk_interpretation": "Алкогольная интерпретация"
    },
    ...
  ],
  "personal_summary": "Персональное резюме для человека с этой датой рождения",
  "astrological_comment": "Астрологический комментарий",
  "recommended_drink": "Рекомендуемый напиток"
}
"""

# Промпт для генерации тестового гадания
PROMPT_TEST_READING = """Сгенерируй тестовое гадание на одной карте Таро с алкогольной тематикой.
Включи:
1. Название карты Таро
2. Краткое описание значения карты
3. Алкогольную интерпретацию карты
4. Короткое послание от таролога (с юмором и алкогольной тематикой)

Верни результат в формате JSON:
{
  "card_name": "Название карты",
  "description": "Описание значения",
  "drunk_interpretation": "Алкогольная интерпретация",
  "tarot_message": "Послание от таролога"
}"""

# Вспомогательные функции для работы с OpenAI API
async def generate_openai_response(prompt, model="gpt-3.5-turbo", temperature=0.7, max_tokens=500):
    """Генерирует ответ от OpenAI API
    
    Args:
        prompt: Текст промпта
        model: Модель OpenAI
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        
    Returns:
        Текст ответа от OpenAI API
    """
    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[{"role": "system", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при запросе к OpenAI API: {e}")
        return None

# Список пользователей, которые получают бесплатный полный расклад
FREE_USERS = [869218484, ]  #218484013 ID пользователей, которым доступен бесплатный расклад

# Создаем роутер для обработки команд гадания
router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    # Создаем клавиатуру с кнопкой "Начать гадать"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔮 Начать гадать", callback_data="start_reading")
    builder.adjust(1)
    
    # Отправляем приветственное сообщение
    await message.answer(
        "🔮 <b>Добро пожаловать в Пьяное Таро!</b> 🍸\n\n"
        "Я - бот-таролог с алкогольным уклоном. Я могу погадать вам на картах Таро "
        "и дать интерпретацию с алкогольной тематикой.\n\n"
        "Нажмите кнопку ниже, чтобы начать гадание:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# Обработчик кнопки "Начать гадать"
@router.callback_query(F.data == "start_reading")
async def start_tarot_reading(callback: CallbackQuery):
    """Обработчик кнопки 'Начать гадать'"""
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()
    
    # Проверяем, находится ли пользователь в списке бесплатных пользователей
    user_id = callback.from_user.id
    if user_id in FREE_USERS:
        # Для пользователей из списка - бесплатный полный расклад через GPT
        await callback.message.answer(
            "🔮 *Специальный расклад Таро* 🔮\n\n"
            "Подготавливаю ваш полный расклад...",
            parse_mode="Markdown"
        )
        
        # Показываем анимацию перед выдачей расклада
        await show_tarot_animation(callback.message)
        
        # Генерируем полный расклад через GPT
        reading = await generate_tarot_reading()
        
        # Отправляем результаты гадания
        await callback.message.answer('🔮 *Ваш расклад готов!* 🍸\n\nВот что говорят карты:', parse_mode="Markdown")
        
        # Отправляем каждую карту с интерпретацией
        for card in reading['cards']:
            await callback.message.answer(
                f"🃏 *{card['name']}*\n\n"
                f"{card['description']}\n\n"
                f"🍸 *Алкогольная интерпретация:*\n{card['drunk_interpretation']}",
                parse_mode="Markdown"
            )
        
        # Отправляем общее толкование
        await callback.message.answer(
            f"🔮 *Общее толкование:*\n\n{reading['summary']}\n\n"
            f"🍸 *Рекомендуемый напиток:*\n"
            f"{reading['recommended_drink']}",
            parse_mode="Markdown"
        )
        
        # Генерируем сообщение от таролога через ChatGPT
        tarot_message = await generate_tarot_message()
        
        # Отправляем сообщение от таролога
        await callback.message.answer(
            f"✨ *Послание таролога:*\n\n{tarot_message}",
            parse_mode="Markdown"
        )
    else:
        # Для обычных пользователей - предложение оплаты
        # Создаем клавиатуру напрямую здесь
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="💳 Оплатить 100 Stars", callback_data="pay_reading")
        builder.button(text="❌ Отмена", callback_data="cancel_reading")
        builder.adjust(1)  # Размещаем кнопки в один столбец
        
        # Отправляем сообщение о начале гадания
        await callback.message.answer(
            "🔮 *Пьяное Таро* 🍸\n\n"
            "Я проведу для вас гадание на картах Таро с алкогольной интерпретацией!\n"
            "Стоимость гадания: 100 Stars.\n\n"
            "Нажмите кнопку ниже, чтобы перейти к оплате.",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )

# Вспомогательные функции для создания клавиатур
def create_keyboard(buttons):
    """Создает клавиатуру с заданными кнопками
    
    Args:
        buttons: Список кортежей (текст, callback_data)
    
    Returns:
        Клавиатура с кнопками
    """
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for text, callback_data in buttons:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(1)  # Размещаем кнопки в один столбец
    return builder.as_markup()

# Создаем клавиатуру с кнопкой оплаты
def create_payment_keyboard():
    """Создает клавиатуру с кнопками оплаты и отмены"""
    buttons = [
        ("💳 Оплатить 100 Stars", "pay_reading"),
        ("❌ Отмена", "cancel_reading")
    ]
    return create_keyboard(buttons)

# Создаем клавиатуру с кнопкой оплаты премиум-гадания
def create_premium_payment_keyboard():
    """Создает клавиатуру с кнопками оплаты премиум и отмены"""
    buttons = [
        ("💳 Оплатить 300 Stars", "pay_premium_reading"),
        ("❌ Отмена", "cancel_reading")
    ]
    return create_keyboard(buttons)

# Создаем клавиатуру для начала гадания
def create_start_reading_keyboard():
    """Создает клавиатуру с кнопкой начала гадания"""
    buttons = [("🔮 Начать гадать", "start_reading")]
    return create_keyboard(buttons)

# Обработчик кнопки "Оплатить"
@router.callback_query(F.data == "pay_reading")
async def pay_tarot_reading(callback: CallbackQuery):
    """Обработчик кнопки 'Оплатить'"""
    await callback.answer()
    try:
        bot = callback.bot
        await bot.send_invoice(
            chat_id=callback.message.chat.id,
            title="Пьяное Таро - Гадание",
            description="Стандартный расклад из 3 карт с алкогольной интерпретацией",
            payload="tarot_reading",
            provider_token="",  # Пустая строка для Telegram Stars
            currency="XTR",
            prices=[
                LabeledPrice(
                    label="Гадание на Таро",
                    amount=100  # 100 Stars
                )
            ],
            start_parameter="tarot_reading",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
            protect_content=False
        )
    except Exception as e:
        print(f"Ошибка при создании счета: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при создании счета. Пожалуйста, попробуйте позже.",
            parse_mode="Markdown"
        )

# Обработчик кнопки "Отмена"
@router.callback_query(F.data == "cancel_reading")
async def cancel_tarot_reading(callback: CallbackQuery):
    """Обработчик кнопки 'Отмена'"""
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()
    
    # Отправляем сообщение об отмене
    await callback.message.answer(
        "❌ Гадание отменено. Вы можете начать снова в любое время.",
        parse_mode="Markdown"
    )

# Обработчик кнопки "Заказать гадание"
@router.callback_query(F.data == "order_reading")
async def order_tarot_reading(callback: CallbackQuery):
    """Обработчик кнопки 'Заказать гадание'"""
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()
    
    # Отправляем сообщение о заказе индивидуального гадания
    await callback.message.answer(
        "💰 *Индивидуальное гадание* 💰\n\n"
        "Вы можете заказать персональное гадание с подробной интерпретацией.\n"
        "Стоимость индивидуального гадания: 300 Stars.\n\n"
        "Гадание будет включать расширенный расклад из 5 карт и детальный анализ вашей ситуации.",
        parse_mode="Markdown",
        reply_markup=create_premium_payment_keyboard()
    )

# Создаем клавиатуру с кнопкой оплаты премиум-гадания
def create_premium_payment_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Оплатить 300 Stars", callback_data="pay_premium_reading")
    builder.button(text="❌ Отмена", callback_data="cancel_reading")
    return builder.as_markup()

# Обработчик кнопки "Оплатить премиум"
@router.callback_query(F.data == "pay_premium_reading")
async def pay_premium_tarot_reading(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Оплатить премиум'"""
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()
    
    # Проверяем, находится ли пользователь в списке бесплатных пользователей
    user_id = callback.from_user.id
    
    # Запрашиваем дату рождения
    await callback.message.answer(
        "🔮 *Индивидуальное гадание* 🔮\n\n"
        "Для составления персонального расклада, пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ (например, 15.05.1990).",
        parse_mode="Markdown"
    )
    
    # Устанавливаем состояние ожидания даты рождения
    await state.set_state(PremiumReadingStates.waiting_for_birthdate)
    
    # Сохраняем информацию о том, является ли пользователь бесплатным
    await state.update_data(is_free_user=(user_id in FREE_USERS))
    
    # Если пользователь в списке FREE_USERS, не создаем счет для оплаты
    if user_id in FREE_USERS:
        return
    
    # Создаем счет для оплаты индивидуального гадания
    # Используем бот из контекста callback
    # Создаем счет с большей суммой и другим описанием
    result = await create_invoice(
        callback.bot, 
        callback.message.chat.id, 
        amount=300,  # 300 Stars
        title="Индивидуальное гадание",
        description="Расширенный расклад из 5 карт с детальным анализом вашей ситуации"
    )
    
    if not result:
        await callback.message.answer(
            "❌ Произошла ошибка при создании счета. Пожалуйста, попробуйте позже.",
            parse_mode="Markdown"
        )

# Пользователи в списке FREE_USERS получают полный расклад без оплаты

# Обработчик кнопки "Тест"
@router.callback_query(F.data == "test_reading")
async def test_tarot_reading(callback: CallbackQuery):
    """Обработчик кнопки 'Тест'"""
    await callback.answer()
    
    # Для всех пользователей - стандартное тестовое гадание
    await callback.message.answer(
        "🧪 *Тестовое гадание* 🧪\n\n"
        "Это бесплатное демо-гадание на одной карте.\n"
        "Вы получите базовую интерпретацию с алкогольной тематикой.\n\n"
        "Подготавливаю вашу карту..."
    )
    await show_tarot_animation(callback.message)
    
    try:
        # Генерируем тестовое гадание полностью через ChatGPT
        prompt = """Сгенерируй тестовое гадание на одной карте Таро с алкогольной тематикой.
        Включи:
        1. Название карты Таро
        2. Краткое описание значения карты
        3. Алкогольную интерпретацию карты
        4. Короткое послание от таролога (с юмором и алкогольной тематикой)
        
        Верни результат в формате JSON:
        {
          "card_name": "Название карты",
          "description": "Описание значения",
          "drunk_interpretation": "Алкогольная интерпретация",
          "tarot_message": "Послание от таролога"
        }"""
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        # Получаем текст ответа
        reading_text = response.choices[0].message.content
        
        try:
            # Пытаемся распарсить JSON из ответа
            reading_data = json.loads(reading_text)
            
            # Отправляем результат тестового гадания
            await callback.message.answer(
                f"🃏 *{reading_data['card_name']}*\n\n"
                f"{reading_data['description']}\n\n"
                f"🍸 *Алкогольная интерпретация:*\n{reading_data['drunk_interpretation']}",
                parse_mode="Markdown"
            )
            
            # Отправляем сгенерированное сообщение от таролога
            await callback.message.answer(
                f"✨ *Послание таролога:*\n\n{reading_data['tarot_message']}",
                parse_mode="Markdown"
            )
            
            # Предлагаем пользователю начать полное гадание
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔮 Начать гадать", callback_data="start_reading")
            builder.adjust(1)
            await callback.message.answer(
                "Это было демо-гадание. Для полного расклада из 3 карт с рекомендацией напитка, "
                "нажмите кнопку ниже:",
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            # Если не удалось распарсить JSON или найти нужные ключи
            print(f"Ошибка при парсинге JSON в test_tarot_reading: {e}")
            
            # Используем запасные данные
            fallback_card = {
                "card_name": "Шут",
                "description": "Карта Шута символизирует новые начинания, спонтанность и свободу.",
                "drunk_interpretation": "Сегодня вечером вы можете быть немного безрассудны. Попробуйте что-то новое, но не переусердствуйте с алкоголем!",
                "tarot_message": "Звезды подсказывают, что сегодня хороший день для экспериментов. Возможно, стоит попробовать новый коктейль или встретиться с друзьями в необычном месте."
            }
            
            # Отправляем результат с запасными данными
            await callback.message.answer(
                f"🃏 *{fallback_card['card_name']}*\n\n"
                f"{fallback_card['description']}\n\n"
                f"🍸 *Алкогольная интерпретация:*\n{fallback_card['drunk_interpretation']}",
                parse_mode="Markdown"
            )
            
            # Отправляем запасное сообщение от таролога
            await callback.message.answer(
                f"✨ *Послание таролога:*\n\n{fallback_card['tarot_message']}",
                parse_mode="Markdown"
            )
            
            # Предлагаем пользователю начать полное гадание
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔮 Начать гадать", callback_data="start_reading")
            builder.adjust(1)
            await callback.message.answer(
                "Это было демо-гадание. Для полного расклада из 3 карт с рекомендацией напитка, "
                "нажмите кнопку ниже:",
                parse_mode="Markdown",
                reply_markup=builder.as_markup()
            )
    
    except Exception as e:
        # Обрабатываем любые другие ошибки
        print(f"Ошибка в test_tarot_reading: {e}")
        
        # Отправляем сообщение об ошибке
        await callback.message.answer(
            "😔 *Упс! Что-то пошло не так...*\n\n"
            "Карты Таро сегодня капризничают. Пожалуйста, попробуйте еще раз позже.",
            parse_mode="Markdown"
        )


# Рекомендуемые напитки
recommended_drinks = [
    "Виски с колой - классика никогда не подводит!",
    "Мохито - освежающий выбор для новых начинаний.",
    "Кровавая Мэри - идеально для интуитивных решений.",
    "Маргарита - сбалансированный выбор для любой ситуации.",
    "Пина Колада - сладкий вкус успеха ждет вас!"
]

@router.message(Command("reading"))
async def cmd_reading(message: Message):
    """Обработчик команды /reading"""
    await message.answer(
        "🔮 *Пьяное Таро* 🍸\n\n"
        "Я проведу для вас гадание на картах Таро с алкогольной интерпретацией!\n"
        "Стоимость гадания: 100 Stars.\n\n"
        "Нажмите кнопку ниже, чтобы оплатить и получить гадание.",
        parse_mode="Markdown"
    )
    
    # Создаем счет для оплаты
    from aiogram import Bot
    bot = Bot.get_current()
    await create_invoice(bot, message.chat.id)

async def show_tarot_animation(message: Message):
    """Показывает анимацию перемешивания и выбора карт"""
    await message.answer("🔮 Перемешиваю карты...")
    await asyncio.sleep(1)
    await message.answer("🃏 Выбираю карты для вашего расклада...")
    await asyncio.sleep(1)
    await message.answer("✨ Настраиваюсь на вашу энергетику...")
    await asyncio.sleep(1)
    await message.answer("🍸 Добавляю алкогольную интерпретацию...")
    await asyncio.sleep(1)

async def generate_tarot_reading():
    """Генерирует полное гадание на Таро через GPT"""
    try:
        # Получаем карты через GPT
        tarot_cards = await fetch_tarot_cards_gpt()
        
        # Проверяем, что tarot_cards это список и он не пустой
        if not isinstance(tarot_cards, list) or len(tarot_cards) == 0:
            # Если карты не получены, запрашиваем полное гадание напрямую через GPT
            prompt = """Создай полное гадание на Таро с тремя картами. Для каждой карты укажи:
1. Название карты
2. Описание значения карты в контексте гадания
3. Алкогольную интерпретацию (юмористическую)

Также добавь общее толкование расклада и рекомендуемый алкогольный напиток.
Формат ответа должен быть в виде JSON:
{
  "cards": [
    {
      "name": "Название карты",
      "description": "Описание значения",
      "drunk_interpretation": "Алкогольная интерпретация"
    },
    ...
  ],
  "summary": "Общее толкование расклада",
  "recommended_drink": "Рекомендуемый напиток"
}"""
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            try:
                # Пытаемся распарсить JSON из ответа
                reading_text = response.choices[0].message.content
                reading = json.loads(reading_text)
                return reading
            except Exception as e:
                print(f"Ошибка при парсинге JSON из ответа GPT: {e}")
                # Используем fallback карты в случае ошибки
                fallback_cards = [
                    {"name": "Шут", "description": "Новые начинания и приключения", "drunk_interpretation": "Время для спонтанных решений и веселья!"},
                    {"name": "Маг", "description": "Сила воли и манипуляция энергиями", "drunk_interpretation": "Ваши способности усиливаются с каждым бокалом!"},
                    {"name": "Верховная Жрица", "description": "Интуиция и тайные знания", "drunk_interpretation": "Доверьтесь внутреннему голосу, особенно после третьего шота!"}
                ]
                return {
                    "cards": fallback_cards,
                    "summary": "Ваши карты указывают на интересный период в жизни. Доверяйте своей интуиции и будьте открыты новым возможностям.",
                    "recommended_drink": "Виски с колой - классика, которая никогда не подведет."
                }
        else:
            # Если карт меньше 3, используем все имеющиеся
            if len(tarot_cards) < 3:
                selected_cards = tarot_cards
            else:
                selected_cards = random.sample(tarot_cards, 3)
    
        # Генерируем общее толкование через GPT
        cards_info = ", ".join([card["name"] for card in selected_cards])
        prompt = f"""На основе следующих карт Таро создай общее толкование расклада и рекомендуемый алкогольный напиток:
Карты: {cards_info}

Ответ должен содержать:
1. Общее толкование расклада (2-3 предложения)
2. Рекомендуемый алкогольный напиток с кратким юмористическим объяснением

Формат ответа должен быть в виде JSON:
{{
  "summary": "Общее толкование расклада",
  "recommended_drink": "Рекомендуемый напиток с объяснением"
}}"""
    
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            # Пытаемся распарсить JSON из ответа
            interpretation_text = response.choices[0].message.content
            interpretation = json.loads(interpretation_text)
            
            return {
                "cards": selected_cards,
                "summary": interpretation.get("summary", "Ваши карты указывают на интересный период в жизни."),
                "recommended_drink": interpretation.get("recommended_drink", "Виски с колой - классика, которая никогда не подведет.")
            }
        except Exception as e:
            print(f"Ошибка при генерации толкования через GPT: {e}")
            # Используем стандартное толкование в случае ошибки
            return {
                "cards": selected_cards,
                "summary": "Ваши карты указывают на интересный период в жизни. Доверяйте своей интуиции и будьте открыты новым возможностям.",
                "recommended_drink": "Виски с колой - классика, которая никогда не подведет."
            }
    except Exception as e:
        print(f"Общая ошибка при генерации гадания: {e}")
        # Используем fallback карты в случае ошибки
        fallback_cards = [
            {"name": "Шут", "description": "Новые начинания и приключения", "drunk_interpretation": "Время для спонтанных решений и веселья!"},
            {"name": "Маг", "description": "Сила воли и манипуляция энергиями", "drunk_interpretation": "Ваши способности усиливаются с каждым бокалом!"},
            {"name": "Верховная Жрица", "description": "Интуиция и тайные знания", "drunk_interpretation": "Доверьтесь внутреннему голосу, особенно после третьего шота!"}
        ]
        return {
            "cards": fallback_cards,
            "summary": "Ваши карты указывают на интересный период в жизни. Доверяйте своей интуиции и будьте открыты новым возможностям.",
            "recommended_drink": "Виски с колой - классика, которая никогда не подведет."
        }

async def generate_tarot_message():
    """Генерирует сообщение от таролога через ChatGPT API"""
    try:
        response = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": PROMPT_TAROT_MESSAGE}],
                temperature=0.7,
                max_tokens=200
            )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка при генерации сообщения через GPT: {e}")
        # Возвращаем стандартное сообщение в случае ошибки
        return "Карты говорят, что вам стоит выпить что-нибудь крепкое и не принимать важных решений в ближайшее время. Удача улыбнется вам после третьего бокала!"

# Обработчик ввода даты рождения для премиум-гадания
@router.message(PremiumReadingStates.waiting_for_birthdate)
async def process_birthdate(message: Message, state: FSMContext):
    """Обработчик ввода даты рождения для премиум-гадания"""
    # Получаем дату рождения из сообщения
    birthdate = message.text.strip()
    
    # Проверяем формат даты (простая проверка)
    import re
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', birthdate):
        await message.answer(
            "❌ Пожалуйста, введите дату в формате ДД.ММ.ГГГГ (например, 15.05.1990).",
            parse_mode="HTML"
        )
        return
    
    # Сохраняем дату рождения в состоянии
    await state.update_data(birthdate=birthdate)
    
    # Получаем информацию о пользователе из состояния
    user_data = await state.get_data()
    is_free_user = user_data.get('is_free_user', False)
    
    # Сбрасываем состояние
    await state.clear()
    
    # Если пользователь не бесплатный и не оплатил, то ничего не делаем
    # Оплата будет обрабатываться в payment_handlers.py
    if not is_free_user:
        return
    
    # Для бесплатных пользователей сразу показываем гадание с анимацией
    await show_premium_reading_with_animation(message, birthdate)

async def show_premium_reading_with_animation(message: Message, birthdate: str):
    """Показывает премиум-гадание с анимацией и задержками"""
    # Отправляем сообщение о начале гадания
    await message.answer(
        "<b>🔮 Начинаю индивидуальное гадание...</b>",
        parse_mode="HTML"
    )
    
    # Генерируем премиум-гадание
    reading = await generate_premium_reading(birthdate)
    
    # Задержка перед первой картой
    await asyncio.sleep(2)
    
    # Сообщение о перемешивании карт
    shuffling_msg = await message.answer(
        "<b>🃏 Перемешиваю карты...</b>",
        parse_mode="HTML"
    )
    
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
    await shuffling_msg.edit_text(
        "<b>🃏 Снова перемешиваю карты...</b>",
        parse_mode="HTML"
    )
    
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
    await shuffling_msg.edit_text(
        "<b>🃏 Последний раз перемешиваю карты...</b>",
        parse_mode="HTML"
    )
    
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
    await shuffling_msg.edit_text(
        "<b>✨ Поддаюсь небесам и готовлю вердикт...</b>",
        parse_mode="HTML"
    )
    
    # Задержка перед финальным вердиктом
    await asyncio.sleep(4)
    
    # Отправляем персональное резюме и астрологический комментарий
    await message.answer(
        f"<b>🔮 Персональное резюме:</b>\n\n{reading['personal_summary']}\n\n"
        f"<b>🌟 Астрологический комментарий:</b>\n{reading['astrological_comment']}\n\n"
        f"<b>🍸 Рекомендуемый напиток:</b>\n{reading['recommended_drink']}",
        parse_mode="HTML"
    )

async def fetch_tarot_cards_gpt():
    """Получает карты Таро через ChatGPT API"""
