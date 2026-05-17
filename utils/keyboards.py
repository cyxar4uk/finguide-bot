from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu():
    """Главное меню с постоянными кнопками"""
    keyboard = [
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="🗺 Карта действий"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Задайте вопрос или выберите действие"
    )
