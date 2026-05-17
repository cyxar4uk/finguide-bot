"""
Этап 2: Анализ скачанных страниц с помощью Claude
Создаёт качественные FAQ с развёрнутыми ответами
"""
import json
import os
from anthropic import Anthropic
from database.models import Database
import asyncio


class FAPageAnalyzer:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.pages_dir = "data/fa_pages"
        self.output_file = "data/analyzed_faq.json"

        self.faq_data = []
        self.contacts_data = []

    def load_index(self):
        """Загрузить индекс скачанных страниц"""
        index_path = f"{self.pages_dir}/index.json"
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def read_page_text(self, text_path: str) -> str:
        """Прочитать текст страницы"""
        with open(text_path, 'r', encoding='utf-8') as f:
            return f.read()

    def analyze_page_with_claude(self, text: str, url: str) -> dict:
        """Анализ страницы с помощью Claude"""

        prompt = f"""Проанализируй текст страницы сайта Финансового университета и извлеки полезную информацию для студентов.

URL: {url}

ТЕКСТ СТРАНИЦЫ:
{text[:8000]}  # Ограничиваем длину

ЗАДАЧА:
1. Найди все вопросы и ответы (FAQ)
2. Извлеки контактную информацию (телефоны, email, адреса)
3. Определи категорию информации

ФОРМАТ ОТВЕТА (JSON):
{{
  "faq": [
    {{
      "question": "Полный вопрос",
      "answer": "Развёрнутый ответ (можно длинный, до 500 слов)",
      "category": "Категория",
      "keywords": ["ключевое", "слово"]
    }}
  ],
  "contacts": [
    {{
      "service_name": "Название службы",
      "phone": "+7 (xxx) xxx-xx-xx",
      "email": "email@fa.ru",
      "location": "Адрес",
      "working_hours": "Часы работы",
      "description": "Описание"
    }}
  ]
}}

КАТЕГОРИИ:
- Стипендии и выплаты
- Общежитие
- Библиотека
- Документы и справки
- Учебный процесс
- Поступление
- Дополнительное образование
- Контакты
- Общие вопросы

ВАЖНО:
- Ответы должны быть полными и информативными
- Используй информацию из текста, не придумывай
- Если FAQ нет - верни пустой массив
- Телефоны в формате +7 (xxx) xxx-xx-xx
"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Парсим JSON из ответа
            content = response.content[0].text

            # Ищем JSON в ответе
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)

            return {"faq": [], "contacts": []}

        except Exception as e:
            print(f"Error analyzing page: {e}")
            return {"faq": [], "contacts": []}

    def analyze_all_pages(self):
        """Анализировать все скачанные страницы"""
        print("="*80)
        print("FA.RU PAGE ANALYZER WITH CLAUDE")
        print("="*80)

        # Загружаем индекс
        index = self.load_index()
        total_pages = len(index['pages'])

        print(f"Total pages to analyze: {total_pages}")
        print("="*80)

        for i, page_info in enumerate(index['pages'], 1):
            url = page_info['url']
            text_path = page_info['text_path']

            print(f"\n[{i}/{total_pages}] Analyzing: {url}")

            # Читаем текст
            text = self.read_page_text(text_path)

            # Анализируем с Claude
            result = self.analyze_page_with_claude(text, url)

            # Добавляем source_url к каждому FAQ
            for faq in result.get('faq', []):
                faq['source_url'] = url
                self.faq_data.append(faq)

            # Добавляем source_url к каждому контакту
            for contact in result.get('contacts', []):
                contact['source_url'] = url
                self.contacts_data.append(contact)

            print(f"  Found: {len(result.get('faq', []))} FAQ, {len(result.get('contacts', []))} contacts")

            # Сохраняем промежуточные результаты каждые 10 страниц
            if i % 10 == 0:
                self.save_results()

        # Финальное сохранение
        self.save_results()

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)
        print(f"Total FAQ found: {len(self.faq_data)}")
        print(f"Total contacts found: {len(self.contacts_data)}")
        print(f"Results saved to: {self.output_file}")
        print("="*80)

    def save_results(self):
        """Сохранить результаты в JSON"""
        data = {
            "faq": self.faq_data,
            "contacts": self.contacts_data,
            "stats": {
                "total_faq": len(self.faq_data),
                "total_contacts": len(self.contacts_data)
            }
        }

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def save_to_database(self, db_path: str = 'finguide.db'):
        """Сохранить в базу данных"""
        print("\nSaving to database...")
        db = Database(db_path)
        await db.connect()

        # Сохраняем FAQ
        for item in self.faq_data:
            try:
                await db.add_faq(
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'Общие вопросы'),
                    keywords=','.join(item.get('keywords', []))
                )
            except Exception as e:
                print(f"Error saving FAQ: {e}")

        # Сохраняем контакты
        for item in self.contacts_data:
            try:
                await db.add_contact(
                    service_name=item['service_name'],
                    phone=item.get('phone'),
                    email=item.get('email'),
                    location=item.get('location'),
                    working_hours=item.get('working_hours'),
                    description=item.get('description')
                )
            except Exception as e:
                print(f"Error saving contact: {e}")

        await db.close()
        print("Data saved to database!")


def main():
    # ВАЖНО: Укажи свой API ключ Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        print("Example: export ANTHROPIC_API_KEY=sk-ant-...")
        return

    analyzer = FAPageAnalyzer(api_key)
    analyzer.analyze_all_pages()

    # Сохранить в базу?
    print("\nSave to database? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        asyncio.run(analyzer.save_to_database())


if __name__ == "__main__":
    main()
