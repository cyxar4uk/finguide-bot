"""
МАКСИМАЛЬНЫЙ парсер FA.RU - обход ВСЕХ страниц сайта
Рекурсивно обходит все внутренние ссылки
"""
import asyncio
from parsers.parse_fa_ru import FAParser

async def main():
    parser = FAParser()

    # МАКСИМАЛЬНЫЕ НАСТРОЙКИ
    parser.max_pages = 1000  # До 1000 страниц

    print("="*80)
    print("МАКСИМАЛЬНЫЙ ПАРСИНГ FA.RU - ВЕСЬ САЙТ")
    print("="*80)
    print(f"Лимит страниц: {parser.max_pages}")
    print("Будут обработаны ВСЕ внутренние ссылки сайта fa.ru")
    print("Это может занять 30-60 минут")
    print("="*80)
    print("\nНачать? (y/n)")

    response = input().strip().lower()
    if response != 'y':
        print("Отменено")
        return

    # Запускаем парсинг
    await parser.start_parsing()

    # Сохраняем результаты
    print("\nСохранение результатов...")
    parser.save_to_json('data/fa_parsed_data_maximum.json')

    # Показываем статистику
    print("\n" + "="*80)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("="*80)
    print(f"Обработано страниц: {len(parser.visited_urls)}")
    print(f"Найдено FAQ: {len(parser.faq_data)}")
    print(f"Найдено контактов: {len(parser.contacts_data)}")

    # Группируем FAQ по категориям
    categories = {}
    for faq in parser.faq_data:
        cat = faq.get('category', 'Без категории')
        categories[cat] = categories.get(cat, 0) + 1

    print("\nFAQ по категориям:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

    # Показываем топ источников
    sources = {}
    for faq in parser.faq_data:
        url = faq.get('source_url', 'Unknown')
        sources[url] = sources.get(url, 0) + 1

    print("\nТоп-10 источников FAQ:")
    for url, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {count:3d} - {url}")

    print("="*80)

    # Спрашиваем, сохранять ли в базу
    print("\nСохранить данные в базу данных? (y/n)")
    response = input().strip().lower()

    if response == 'y':
        print("Сохранение в базу данных...")
        await parser.save_to_database()
        print("Готово!")
    else:
        print("Данные сохранены только в JSON")

    # Сохраняем список всех посещённых URL
    with open('data/visited_urls.txt', 'w', encoding='utf-8') as f:
        for url in sorted(parser.visited_urls):
            f.write(url + '\n')
    print(f"\nСписок посещённых URL сохранён в data/visited_urls.txt")

if __name__ == "__main__":
    asyncio.run(main())
