"""
Расширенный парсер FA.RU - глубокий обход всего сайта
"""
import asyncio
from parsers.parse_fa_ru import FAParser

async def main():
    parser = FAParser()

    # РАСШИРЕННЫЕ НАСТРОЙКИ
    parser.max_pages = 500  # Увеличиваем до 500 страниц

    print("="*80)
    print("РАСШИРЕННЫЙ ПАРСИНГ FA.RU")
    print("="*80)
    print(f"Максимум страниц: {parser.max_pages}")
    print(f"Приоритетных разделов: {len(parser.priority_sections)}")
    print("\nПриоритетные разделы:")
    for section in parser.priority_sections:
        print(f"  - {section}")
    print("="*80)

    # Запускаем парсинг
    await parser.start_parsing()

    # Сохраняем результаты
    print("\nСохранение результатов...")
    parser.save_to_json('data/fa_parsed_data_full.json')

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

if __name__ == "__main__":
    asyncio.run(main())
