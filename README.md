# FinGuide Bot

> **EN:** FinGuide is a Telegram bot that helps first-year students settle into university life. It personalizes answers by faculty and course, searches a knowledge base with typo-tolerant fuzzy matching (RapidFuzz + synonym expansion), shows service contacts and an "action map" for typical situations. aiogram 3 + SQLite, ships with a Dockerfile, demo seed data and web parsers for collecting source material. Unofficial student project.

> **Дисклеймер.** Проект не является официальным продуктом Финансового университета при Правительстве РФ (fa.ru) и не связан с ним. Название университета и его контактные данные используются только для описания назначения бота. Скачанные страницы сайта и собранная из них рабочая база знаний в репозиторий не включены; в комплекте — небольшой демонстрационный набор данных.

Телеграм-бот [@FinGuide1_bot](https://t.me/FinGuide1_bot) для помощи студентам в адаптации: где взять студенческий билет, как получить стипендию, как попасть в общежитие, кому звонить.

## Зачем

Информация для студентов разбросана по сайту вуза, чатам и «сарафанному радио». Бот собирает ответы в одном месте и показывает те, что относятся к факультету и курсу пользователя.

## Возможности

- **Персонализация**: при `/start` пользователь выбирает факультет и курс; FAQ можно привязать к факультету/курсу или оставить общими.
- **Нечёткий поиск** (RapidFuzz): `token_set_ratio`, `partial_ratio`, `token_sort_ratio`, поиск также по ответу и категории; устойчив к опечаткам и порядку слов.
- **Синонимы**: «общага», «студак», «пары» и т. п. расширяют запрос до канонических терминов.
- **Похожие вопросы** — до трёх inline-кнопок под ответом.
- **Контакты служб** по категориям и **карта действий** (`/contacts`, `/map`).
- **Профиль и меню**: `/start`, `/profile`, `/search`, `/help`, постоянная клавиатура.
- **Парсеры сайта** (`parsers/`): скачивание страниц fa.ru, извлечение FAQ по шаблонам, опциональный разбор через Anthropic API — для наполнения собственной базы знаний.

## Архитектура

```
Telegram  <->  aiogram 3 (bot.py: polling, DB middleware)
                 |- handlers/registration.py  профиль, меню, /help
                 |- handlers/search.py        свободный текстовый вопрос -> SmartSearch
                 |- handlers/contacts.py      контакты, карта действий
                 |- utils/search.py           SmartSearch (RapidFuzz + синонимы)
                 `- database/models.py        SQLite через aiosqlite: users, faq, contacts
parsers/  ->  data/fa_pages (локально)  ->  FAQ в БД
```

Подробнее: [`docs/developer-guide.md`](docs/developer-guide.md), [`docs/action-map.md`](docs/action-map.md), [`docs/parsing.md`](docs/parsing.md).

## Стек

Python 3.12, aiogram 3.7, aiosqlite, RapidFuzz, python-dotenv, aiohttp + BeautifulSoup4 + lxml (парсеры), Docker.

## Быстрый старт

1. Создайте бота у [@BotFather](https://t.me/BotFather) и скопируйте токен.
2. `cp .env.example .env` и впишите `BOT_TOKEN`.

**Локально**

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py     # демо-данные: 11 FAQ и 8 контактов
python bot.py
```

**Docker**

```bash
docker compose up -d --build
```

При первом запуске контейнер сам заполнит БД демо-данными; БД хранится в томе `finguide-db`.

Для Windows есть лаунчеры `scripts/start_bot.bat` и `scripts/start_docker.bat`.

## Конфигурация

| Переменная | Обязательна | Описание |
|---|---|---|
| `BOT_TOKEN` | да | токен Telegram-бота |
| `DATABASE_PATH` | нет | путь к SQLite-файлу, по умолчанию `finguide.db` |
| `ANTHROPIC_API_KEY` | нет | только для `parsers/analyze_fa_pages.py` (нужен `pip install anthropic`) |

Наполнение базы: методы `Database.add_faq(...)` и `Database.add_contact(...)`, примеры — в `seed_data.py`.

## Тесты

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Парсеры

Запускаются из корня: `python -m parsers.download_fa_pages`, `python -m parsers.quick_analyze` и т. д. Результаты сохраняются в `data/` и в git не попадают. Перед сбором данных проверьте условия использования сайта и соблюдайте разумную нагрузку; публиковать чужой контент не следует. См. [`docs/parsing.md`](docs/parsing.md).

## Структура

```
bot.py  seed_data.py  Dockerfile  docker-compose.yml  requirements*.txt
database/   handlers/   utils/      код бота
parsers/    парсеры и анализаторы сайта
scripts/    Windows-лаунчеры
tests/      pytest
docs/       developer-guide, action-map, parsing
data/       локальные данные парсеров (не публикуются)
```

## Лицензия

[MIT](LICENSE) © 2026 Ilia Melnikov. Лицензия распространяется на код; контент сайта fa.ru принадлежит его правообладателям.
