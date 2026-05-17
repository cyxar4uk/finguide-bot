from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Database
from utils.constants import CONTACT_CATEGORIES
from utils.keyboards import get_main_menu


router = Router()


def get_categories_keyboard():
    buttons = [
        [InlineKeyboardButton(text=cat, callback_data=f"contact_cat:{cat}")]
        for cat in CONTACT_CATEGORIES
    ]
    buttons.append([InlineKeyboardButton(text="📋 Все контакты", callback_data="contact_cat:all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("contacts"))
async def cmd_contacts(message: Message):
    await message.answer(
        "📞 <b>Контакты служб Финансового университета</b>\n\n"
        "🎓 <b>Основные контакты:</b>\n"
        "• Приемная комиссия: +7 (495) 249-52-49\n"
        "• Email: priemka@fa.ru\n"
        "• Адрес: Ленинградский пр-т, д.51/1\n"
        "• Часы работы: Пн-Пт 9:30-17:30\n\n"
        "Выбери категорию для подробных контактов:",
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("contact_cat:"))
async def show_contacts(callback: CallbackQuery, db: Database):
    category = callback.data.split(":", 1)[1]

    if category == "all":
        contacts = await db.get_contacts()
    else:
        contacts = await db.get_contacts(category)

    if not contacts:
        await callback.message.edit_text(
            "😔 Контакты не найдены.",
            reply_markup=get_categories_keyboard()
        )
        await callback.answer()
        return

    response = f"📞 <b>{category if category != 'all' else 'Все контакты'}</b>\n\n"

    for contact in contacts:
        response += f"<b>{contact['service_name']}</b>\n"

        if contact['description']:
            response += f"{contact['description']}\n"

        if contact['phone']:
            response += f"📱 {contact['phone']}\n"

        if contact['email']:
            response += f"📧 {contact['email']}\n"

        if contact['location']:
            response += f"📍 {contact['location']}\n"

        if contact['working_hours']:
            response += f"🕐 {contact['working_hours']}\n"

        response += "\n"

    # Добавляем кнопку "Назад"
    back_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="contacts_back")]
    ])

    await callback.message.edit_text(response, reply_markup=back_button, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "contacts_back")
async def contacts_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 <b>Контакты служб Финансового университета</b>\n\n"
        "🎓 <b>Основные контакты:</b>\n"
        "• Приемная комиссия: +7 (495) 249-52-49\n"
        "• Email: priemka@fa.ru\n"
        "• Адрес: Ленинградский пр-т, д.51/1\n"
        "• Часы работы: Пн-Пт 9:30-17:30\n\n"
        "Выбери категорию для подробных контактов:",
        reply_markup=get_categories_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("map"))
async def cmd_map(message: Message):
    map_text = """
🗺 <b>Карта действий для типовых ситуаций</b>

<b>🎓 Поступление:</b>
1. Приемная комиссия: +7 (495) 249-52-49
2. Email: priemka@fa.ru
3. Адрес: Ленинградский пр-т, д.51/1
4. Часы работы: Пн-Пт 9:30-17:30

<b>💰 Перейти на бюджет:</b>
1. Нужны отличные/хорошие оценки
2. Или льготная категория (сироты, дети участников СВО и др.)
3. Подать заявление в комиссию
4. Ждать решения при наличии вакантных мест

<b>💳 Оплата обучения:</b>
1. Онлайн-оплата на сайте fa.ru
2. Или оплата по квитанции
3. Доступны: рассрочка, отсрочка, скидки
4. Скан квитанции отправлять не нужно

<b>💼 Найти стажировку:</b>
1. Раздел "Трудоустройство" на fa.ru
2. Доступны: Газпромбанк, ДОМ.РФ, МКБ, ПСБ
3. Зарплата от 41 900₽, гибкий график
4. Можно совмещать с учебой

<b>📝 Получить справку:</b>
1. Студенческий офис или личный кабинет
2. Деканат для академических справок
3. Срок изготовления: 3-5 дней

<b>📚 Взять книгу:</b>
1. Электронная библиотека через личный кабинет
2. Библиотека в корпусе (по читательскому билету)
3. Продление онлайн или лично

<b>🏠 Вопросы по общежитию:</b>
1. Комендант общежития
2. Отдел по работе с общежитиями
3. Оплата через сайт fa.ru

<b>🌍 Учеба за рубежом:</b>
1. Отдел международной деятельности
2. Программы: обмен, двойной диплом, летние школы
3. Стипендии и гранты доступны

<b>📖 Дополнительное образование:</b>
1. Центр StudUp для студентов
2. Институты ДПО для всех
3. Скидки для студентов университета

<b>🔬 Научная деятельность:</b>
1. Научное студенческое общество (НСО)
2. Совет молодых ученых
3. Участие в конференциях и публикациях

<b>🆘 Нужна помощь:</b>
• Психологическая служба (бесплатно)
• Медпункт в главном корпусе
• Материальная помощь через деканат

Используй 📞 Контакты или задай вопрос боту для подробностей!
"""
    await message.answer(map_text, parse_mode="HTML", reply_markup=get_main_menu())
