# FinGuide Bot — Документация для разработчика

## 📋 Содержание

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура](#архитектура)
3. [Установка и настройка](#установка-и-настройка)
4. [Структура кодовой базы](#структура-кодовой-базы)
5. [База данных](#база-данных)
6. [Добавление функционала](#добавление-функционала)
7. [Деплой](#деплой)
8. [Troubleshooting](#troubleshooting)

---

## Обзор проекта

**FinGuide** — Telegram-бот для помощи студентам в адаптации к университетской жизни.

### Основные возможности:
- 🎯 **Персонализация** — учёт факультета и курса студента
- 🔍 **Умный поиск** — нечёткий поиск по базе знаний (RapidFuzz)
- 📞 **Контакты служб** — структурированный справочник
- 🗺 **Карта действий** — пошаговые инструкции для типовых ситуаций
- ⌨️ **Постоянное меню** — быстрый доступ к функциям
- 🔘 **Inline-кнопки** — похожие вопросы как кнопки для быстрого выбора

### Технологический стек:
- **Python 3.12+**
- **aiogram 3.7** — асинхронный фреймворк для Telegram Bot API
- **SQLite** — база данных (через aiosqlite)
- **RapidFuzz 3.9** — нечёткий поиск по тексту
- **python-dotenv** — управление переменными окружения

---

## Архитектура

### Общая схема:

```
┌─────────────┐
│  Telegram   │
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         bot.py (main)               │
│  - Инициализация бота               │
│  - Регистрация роутеров             │
│  - Middleware для БД                │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Handlers (роутеры)          │
│  - registration.py (профиль)        │
│  - search.py (умный поиск)          │
│  - contacts.py (контакты, карта)    │
└──────┬──────────────────────────────┘
       │
       ├──────────────┬─────────────────┐
       ▼              ▼                 ▼
┌──────────┐   ┌──────────┐    ┌──────────┐
│ Database │   │  Search  │    │Keyboards │
│  models  │   │  Engine  │    │  utils   │
└──────────┘   └──────────┘    └──────────┘
       │
       ▼
┌──────────────┐
│  SQLite DB   │
│ finguide.db  │
└──────────────┘
```

### Поток данных:

1. **Пользователь** отправляет сообщение в Telegram
2. **bot.py** получает update через aiogram
3. **Middleware** добавляет объект БД в контекст
4. **Router** обрабатывает сообщение (registration/search/contacts)
5. **Handler** взаимодействует с БД и утилитами
6. **Ответ** отправляется пользователю

---

## Установка и настройка

### 1. Клонирование и установка зависимостей

```bash
cd finguide-bot
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создай файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируй `.env`:

```env
BOT_TOKEN=your_bot_token_here
DATABASE_PATH=finguide.db
```

**Получение токена бота:**
1. Найди [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot`
3. Следуй инструкциям
4. Скопируй токен в `.env`

### 3. Инициализация базы данных

```bash
# Создать таблицы и заполнить тестовыми данными
python seed_data.py


```

### 4. Запуск бота

```bash
# Запуск в foreground (для разработки)
python bot.py

# Запуск в background (для продакшена)
nohup python bot.py > bot.log 2>&1 &
```

### 5. Проверка работы

1. Найди своего бота в Telegram по username
2. Отправь `/start`
3. Пройди регистрацию
4. Задай тестовый вопрос

---

## Структура кодовой базы

```
finguide-bot/
├── bot.py                      # Главный файл, точка входа
├── seed_data.py               # Скрипт заполнения БД начальными данными
├── requirements.txt           # Зависимости Python
├── .env                       # Конфигурация (не в git!)
├── .env.example              # Шаблон конфигурации
├── .gitignore                # Игнорируемые файлы
├── finguide.db               # База данных SQLite (создаётся автоматически)
│
├── database/
│   ├── __init__.py
│   └── models.py             # Модели БД и методы работы с данными
│
├── handlers/
│   ├── __init__.py
│   ├── registration.py       # Регистрация, профиль, меню, /start, /help
│   ├── search.py            # Умный поиск, обработка вопросов
│   └── contacts.py          # Контакты служб, карта действий
│
├── utils/
│   ├── __init__.py
│   ├── constants.py         # Константы (факультеты, категории)
│   ├── search.py           # Логика умного поиска (RapidFuzz)
│   └── keyboards.py        # Клавиатуры (ReplyKeyboard, InlineKeyboard)
│
└── data/                    # Директория для дополнительных данных (пусто)
```

### Описание ключевых файлов:

#### `bot.py`
Главный файл приложения. Инициализирует бота, регистрирует роутеры, настраивает middleware.

```python
# Основные компоненты:
- Bot() — объект бота
- Dispatcher() — диспетчер событий
- Database() — подключение к БД
- Middleware — передача БД в handlers
```

#### `database/models.py`
Класс `Database` с методами для работы с SQLite:

```python
# Основные методы:
- create_tables() — создание таблиц
- get_user() — получить пользователя
- create_user() — создать пользователя
- update_user_profile() — обновить профиль
- search_faq() — поиск FAQ с фильтрацией
- get_contacts() — получить контакты
- add_faq() — добавить FAQ
- add_contact() — добавить контакт
```

#### `handlers/registration.py`
Обработчики регистрации и профиля:

```python
# Основные handlers:
- cmd_start() — /start, регистрация
- process_faculty() — выбор факультета
- process_course() — выбор курса
- cmd_profile() — /profile, просмотр профиля
- cmd_help() — /help, справка
- menu_* — обработчики кнопок меню
```

#### `handlers/search.py`
Умный поиск по базе знаний:

```python
# Основные handlers:
- cmd_search() — /search, инструкция
- handle_question() — обработка текстовых вопросов
- handle_faq_button() — обработка нажатий на inline-кнопки
```

#### `handlers/contacts.py`
Контакты и карта действий:

```python
# Основные handlers:
- cmd_contacts() — /contacts, выбор категории
- show_contacts() — показ контактов по категории
- contacts_back() — возврат к выбору категории
- cmd_map() — /map, карта действий
```

#### `utils/search.py`
Класс `SmartSearch` для нечёткого поиска:

```python
# Основные методы:
- search() — поиск с порогом совпадения
- find_best_match() — лучшее совпадение
```

#### `utils/keyboards.py`
Генераторы клавиатур:

```python
# Основные функции:
- get_main_menu() — постоянное меню (ReplyKeyboard)
```

---

## База данных

### Схема таблиц:

#### `users`
Хранит информацию о пользователях.

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,        -- Telegram ID
    username TEXT,                      -- Telegram username
    first_name TEXT,                    -- Имя
    faculty TEXT,                       -- Факультет
    course INTEGER,                     -- Курс (1-5)
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `faq`
База знаний с вопросами и ответами.

```sql
CREATE TABLE faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,             -- Вопрос
    answer TEXT NOT NULL,               -- Ответ
    faculty TEXT,                       -- Факультет (NULL = для всех)
    course INTEGER,                     -- Курс (NULL = для всех)
    category TEXT,                      -- Категория
    keywords TEXT                       -- Ключевые слова для поиска
);
```

#### `contacts`
Контакты служб университета.

```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name TEXT NOT NULL,         -- Название службы
    description TEXT,                   -- Описание
    phone TEXT,                         -- Телефон
    email TEXT,                         -- Email
    location TEXT,                      -- Местоположение
    working_hours TEXT,                 -- Часы работы
    category TEXT                       -- Категория
);
```

### Работа с БД:

#### Добавление FAQ:

```python
await db.add_faq(
    question="Как получить справку?",
    answer="Обратитесь в деканат...",
    category="Документы",
    faculty="Информационные технологии",  # Опционально
    course=1,                              # Опционально
    keywords="справка, документы, деканат"
)
```

#### Добавление контакта:

```python
await db.add_contact(
    service_name="Деканат ИТ",
    description="Общие вопросы",
    phone="+7 (495) 123-45-67",
    email="dekanat@university.ru",
    location="Корпус А, 3 этаж, каб. 305",
    working_hours="Пн-Пт 9:00-17:00",
    category="Деканат"
)
```

#### Поиск FAQ с персонализацией:

```python
# Получить FAQ для конкретного факультета и курса
faq_items = await db.search_faq(
    query="стипендия",
    faculty="Информационные технологии",
    course=2
)
# Вернёт FAQ для ИТ 2 курса + общие FAQ (где faculty=NULL, course=NULL)
```

---

## Добавление функционала

### 1. Добавление новой команды

**Шаг 1:** Создай handler в соответствующем файле (или создай новый):

```python
# handlers/new_feature.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from utils.keyboards import get_main_menu

router = Router()

@router.message(Command("mycommand"))
async def cmd_mycommand(message: Message):
    await message.answer(
        "Ответ на команду",
        reply_markup=get_main_menu()
    )
```

**Шаг 2:** Зарегистрируй роутер в `bot.py`:

```python
from handlers import registration, search, contacts, new_feature

# ...

dp.include_router(registration.router)
dp.include_router(search.router)
dp.include_router(contacts.router)
dp.include_router(new_feature.router)  # Добавь сюда
```

### 2. Добавление кнопки в меню

Отредактируй `utils/keyboards.py`:

```python
def get_main_menu():
    keyboard = [
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="📞 Контакты")],
        [KeyboardButton(text="🗺 Карта действий"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="❓ Помощь"), KeyboardButton(text="🆕 Новая кнопка")],  # Добавь
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Задайте вопрос или выберите действие"
    )
```

Добавь обработчик в `handlers/registration.py`:

```python
@router.message(F.text == "🆕 Новая кнопка")
async def menu_new_button(message: Message):
    await message.answer("Обработка новой кнопки", reply_markup=get_main_menu())
```

### 3. Добавление новой категории FAQ

**Шаг 1:** Добавь категорию в `utils/constants.py`:

```python
FAQ_CATEGORIES = [
    "Общие вопросы",
    "Учебный процесс",
    # ...
    "Новая категория",  # Добавь сюда
]
```

**Шаг 2:** Добавь FAQ с новой категорией:

```python
await db.add_faq(
    question="Вопрос",
    answer="Ответ",
    category="Новая категория"
)
```

### 4. Изменение порога поиска

Отредактируй `handlers/search.py`:

```python
# Текущее значение: 60 (60% совпадения)
search_engine = SmartSearch(threshold=60)

# Для более строгого поиска:
search_engine = SmartSearch(threshold=80)

# Для более мягкого поиска:
search_engine = SmartSearch(threshold=40)
```

### 5. Добавление факультета

Отредактируй `utils/constants.py`:

```python
FACULTIES = [
    "Информационные технологии",
    "Экономика и управление",
    # ...
    "Новый факультет",  # Добавь сюда
]
```

---

## Деплой

### Вариант 1: VPS (Ubuntu/Debian)

#### 1. Установка зависимостей:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

#### 2. Клонирование проекта:

```bash
git clone <your-repo-url> finguide-bot
cd finguide-bot
```

#### 3. Создание виртуального окружения:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Настройка `.env`:

```bash
nano .env
# Вставь токен бота
```

#### 5. Инициализация БД:

```bash
python seed_data.py
```

#### 6. Запуск через systemd:

Создай файл `/etc/systemd/system/finguide-bot.service`:

```ini
[Unit]
Description=FinGuide Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/finguide-bot
Environment="PATH=/path/to/finguide-bot/venv/bin"
ExecStart=/path/to/finguide-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запусти сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable finguide-bot
sudo systemctl start finguide-bot
sudo systemctl status finguide-bot
```

Логи:

```bash
sudo journalctl -u finguide-bot -f
```

### Вариант 2: Docker

Создай `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Создай `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    restart: always
    env_file:
      - .env
    volumes:
      - ./finguide.db:/app/finguide.db
```

Запуск:

```bash
docker-compose up -d
docker-compose logs -f
```

### Вариант 3: Heroku

1. Создай `Procfile`:

```
worker: python bot.py
```

2. Создай `runtime.txt`:

```
python-3.12.0
```

3. Деплой:

```bash
heroku login
heroku create finguide-bot
heroku config:set BOT_TOKEN=your_token_here
git push heroku main
heroku ps:scale worker=1
heroku logs --tail
```

---

## Troubleshooting

### Проблема: Бот не отвечает

**Решение:**
1. Проверь, что бот запущен: `ps aux | grep bot.py`
2. Проверь логи: `tail -f bot.log` или `journalctl -u finguide-bot -f`
3. Проверь токен в `.env`
4. Проверь интернет-соединение

### Проблема: База данных не найдена

**Решение:**
1. Запусти `python seed_data.py`
2. Проверь путь в `.env`: `DATABASE_PATH=finguide.db`
3. Проверь права доступа: `chmod 644 finguide.db`

### Проблема: Поиск не находит вопросы

**Решение:**
1. Проверь порог поиска в `handlers/search.py` (попробуй снизить до 40-50)
2. Проверь, что FAQ добавлены: `sqlite3 finguide.db "SELECT COUNT(*) FROM faq;"`
3. Добавь ключевые слова в FAQ для лучшего поиска

### Проблема: Кнопки меню не работают

**Решение:**
1. Проверь, что обработчики зарегистрированы в `handlers/registration.py`
2. Проверь фильтр: `F.text == "🔍 Поиск"` (точное совпадение с текстом кнопки)
3. Перезапусти бота

### Проблема: UnicodeEncodeError в Windows

**Решение:**
1. Убери эмодзи из `print()` в скриптах
2. Или добавь в начало скрипта:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

### Проблема: Конфликт версий pydantic

**Решение:**
Это не критично для работы бота. Если нужно исправить:
```bash
pip install --upgrade pydantic
```

---

## Полезные команды

### Работа с БД:

```bash
# Открыть БД в SQLite CLI
sqlite3 finguide.db

# Посмотреть все таблицы
.tables

# Посмотреть структуру таблицы
.schema users

# Посмотреть все FAQ
SELECT * FROM faq;

# Посмотреть количество пользователей
SELECT COUNT(*) FROM users;

# Удалить все данные (осторожно!)
DELETE FROM faq;
DELETE FROM users;
DELETE FROM contacts;
```

### Работа с ботом:

```bash
# Запуск
python bot.py

# Запуск в фоне
nohup python bot.py > bot.log 2>&1 &

# Остановка
pkill -f "python bot.py"

# Просмотр логов
tail -f bot.log

# Перезапуск
pkill -f "python bot.py" && nohup python bot.py > bot.log 2>&1 &
```

### Работа с зависимостями:

```bash
# Установка
pip install -r requirements.txt

# Обновление
pip install --upgrade -r requirements.txt

# Добавление новой зависимости
pip install package_name
pip freeze > requirements.txt
```

---

## Контакты и поддержка

- **Telegram бота:** @FinGuide1_bot
- **Токен:** `<ваш токен от @BotFather>`

### Полезные ссылки:

- [Документация aiogram 3.x](https://docs.aiogram.dev/en/latest/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [RapidFuzz документация](https://maxbachmann.github.io/RapidFuzz/)
- [SQLite документация](https://www.sqlite.org/docs.html)

---

**Удачи в разработке! 🚀**
