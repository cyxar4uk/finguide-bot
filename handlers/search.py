from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Database
from utils.search import SmartSearch
from utils.keyboards import get_main_menu


router = Router()
search_engine = SmartSearch(threshold=50)


@router.message(Command("search"))
async def cmd_search(message: Message):
    await message.answer(
        "🔍 <b>Умный поиск</b>\n\n"
        "Просто напиши свой вопрос, и я найду ответ!\n\n"
        "Примеры:\n"
        "• Как получить стипендию?\n"
        "• Где библиотека?\n"
        "• Как записаться в общежитие?",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


@router.message(F.text & ~F.text.startswith("/") & ~F.text.in_(["🔍 Поиск", "📞 Контакты", "🗺 Карта действий", "👤 Профиль", "❓ Помощь"]))
async def handle_question(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer("Используй /start для начала работы.", reply_markup=get_main_menu())
        return

    # Получаем FAQ с учётом персонализации
    faq_items = await db.search_faq(
        message.text,
        faculty=user.get("faculty"),
        course=user.get("course")
    )

    if not faq_items:
        await message.answer(
            "😔 К сожалению, я не нашёл ответа на твой вопрос.\n\n"
            "Попробуй:\n"
            "• Переформулировать вопрос\n"
            "• Использовать 📞 Контакты для поиска нужной службы\n"
            "• Обратиться к куратору",
            reply_markup=get_main_menu()
        )
        return

    # Ищем лучшее совпадение
    results = search_engine.search(message.text, faq_items)

    if not results:
        await message.answer(
            "🤔 Не нашёл точного ответа.\n\n"
            "Используй 📞 Контакты для связи со службами университета.",
            reply_markup=get_main_menu()
        )
        return

    # Показываем лучший результат
    best = results[0]
    response = f"💡 <b>{best['question']}</b>\n\n{best['answer']}"

    if best['category']:
        response += f"\n\n📂 Категория: {best['category']}"

    # Создаём кнопки с похожими вопросами
    keyboard = None
    if len(results) > 1:
        response += "\n\n<b>Похожие вопросы:</b>"
        buttons = []
        for i, result in enumerate(results[1:4], 1):  # Показываем до 3 похожих
            # Используем хеш вопроса как ID для callback
            question_id = str(hash(result['question']))[-8:]
            buttons.append([InlineKeyboardButton(
                text=f"{i}. {result['question'][:60]}{'...' if len(result['question']) > 60 else ''}",
                callback_data=f"faq:{question_id}"
            )])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("faq:"))
async def handle_faq_button(callback: CallbackQuery, db: Database):
    """Обработчик нажатия на кнопку с похожим вопросом"""
    question_id = callback.data.split(":")[1]

    user = await db.get_user(callback.from_user.id)

    # Получаем все FAQ
    faq_items = await db.search_faq(
        "",
        faculty=user.get("faculty") if user else None,
        course=user.get("course") if user else None
    )

    # Ищем вопрос по ID
    target_question = None
    for item in faq_items:
        if str(hash(item[0]))[-8:] == question_id:
            target_question = item
            break

    if not target_question:
        await callback.answer("Вопрос не найден", show_alert=True)
        return

    # Показываем ответ
    response = f"💡 <b>{target_question[0]}</b>\n\n{target_question[1]}"

    if target_question[2]:
        response += f"\n\n📂 Категория: {target_question[2]}"

    # Ищем другие похожие вопросы
    results = search_engine.search(target_question[0], faq_items)

    keyboard = None
    if len(results) > 1:
        response += "\n\n<b>Похожие вопросы:</b>"
        buttons = []
        for i, result in enumerate(results[1:4], 1):
            question_id_new = str(hash(result['question']))[-8:]
            buttons.append([InlineKeyboardButton(
                text=f"{i}. {result['question'][:60]}{'...' if len(result['question']) > 60 else ''}",
                callback_data=f"faq:{question_id_new}"
            )])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        # Message is the same, just answer the callback
        pass
    await callback.answer()
