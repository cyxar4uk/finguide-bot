from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Database
from utils.constants import FACULTIES, COURSES
from utils.keyboards import get_main_menu


class Registration(StatesGroup):
    waiting_for_faculty = State()
    waiting_for_course = State()


router = Router()


def get_faculty_keyboard():
    buttons = [
        [InlineKeyboardButton(text=faculty, callback_data=f"faculty:{i}")]
        for i, faculty in enumerate(FACULTIES)
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_course_keyboard():
    buttons = [
        [InlineKeyboardButton(text=f"{course} курс", callback_data=f"course:{course}")]
        for course in COURSES
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, db: Database):
    user = await db.get_user(message.from_user.id)

    if user and user["faculty"] and user["course"]:
        await message.answer(
            f"С возвращением, {message.from_user.first_name}!\n\n"
            f"📚 Факультет: {user['faculty']}\n"
            f"🎓 Курс: {user['course']}\n\n"
            "Выбери действие из меню или просто задай вопрос!",
            reply_markup=get_main_menu()
        )
    else:
        await db.create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋\n\n"
            "Я FinGuide — твой помощник в студенческой жизни.\n\n"
            "Давай настроим твой профиль. Выбери свой факультет:",
            reply_markup=get_faculty_keyboard()
        )
        await state.set_state(Registration.waiting_for_faculty)


@router.callback_query(F.data.startswith("faculty:"), Registration.waiting_for_faculty)
async def process_faculty(callback: CallbackQuery, state: FSMContext):
    faculty_idx = int(callback.data.split(":")[1])
    faculty = FACULTIES[faculty_idx]

    await state.update_data(faculty=faculty)
    await callback.message.edit_text(
        f"✅ Факультет: {faculty}\n\n"
        "Теперь выбери свой курс:",
        reply_markup=get_course_keyboard()
    )
    await state.set_state(Registration.waiting_for_course)
    await callback.answer()


@router.callback_query(F.data.startswith("course:"), Registration.waiting_for_course)
async def process_course(callback: CallbackQuery, state: FSMContext, db: Database):
    course = int(callback.data.split(":")[1])
    data = await state.get_data()
    faculty = data["faculty"]

    await db.update_user_profile(callback.from_user.id, faculty, course)

    await callback.message.edit_text(
        f"✅ Профиль настроен!\n\n"
        f"📚 Факультет: {faculty}\n"
        f"🎓 Курс: {course}\n\n"
        "Теперь я буду показывать тебе только релевантную информацию."
    )

    # Отправляем новое сообщение с меню
    await callback.message.answer(
        "Выбери действие из меню или просто задай вопрос!",
        reply_markup=get_main_menu()
    )

    await state.clear()
    await callback.answer()


@router.message(Command("profile"))
async def cmd_profile(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer("Используй /start для регистрации.")
        return

    await message.answer(
        f"👤 Твой профиль:\n\n"
        f"📚 Факультет: {user['faculty'] or 'Не указан'}\n"
        f"🎓 Курс: {user['course'] or 'Не указан'}\n\n"
        "Для изменения профиля используй /start",
        reply_markup=get_main_menu()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = """
🤖 <b>Команды FinGuide:</b>

/start — Начать работу / настроить профиль
/help — Показать это сообщение
/profile — Посмотреть свой профиль
/search — Поиск по базе знаний
/contacts — Контакты служб университета
/map — Карта действий для типовых ситуаций

💡 <b>Умный поиск:</b>
Просто напиши свой вопрос, и я найду ответ!

Примеры:
• "Как получить стипендию?"
• "Где находится библиотека?"
• "Как записаться в общежитие?"
"""
    await message.answer(help_text, parse_mode="HTML", reply_markup=get_main_menu())


# Обработчики кнопок меню
@router.message(F.text == "🔍 Поиск")
async def menu_search(message: Message):
    await cmd_search_info(message)


@router.message(F.text == "📞 Контакты")
async def menu_contacts(message: Message):
    from handlers.contacts import cmd_contacts
    await cmd_contacts(message)


@router.message(F.text == "🗺 Карта действий")
async def menu_map(message: Message):
    from handlers.contacts import cmd_map
    await cmd_map(message)


@router.message(F.text == "👤 Профиль")
async def menu_profile(message: Message, db: Database):
    await cmd_profile(message, db)


@router.message(F.text == "❓ Помощь")
async def menu_help(message: Message):
    await cmd_help(message)


async def cmd_search_info(message: Message):
    await message.answer(
        "🔍 <b>Умный поиск</b>\n\n"
        "Просто напиши свой вопрос, и я найду ответ!\n\n"
        "Примеры:\n"
        "• Как получить стипендию?\n"
        "• Где библиотека?\n"
        "• Документы для миграционного учета?\n"
        "• Где смотреть баллы?",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
