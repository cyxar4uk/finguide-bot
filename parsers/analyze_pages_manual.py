"""
Ручной анализ страниц для создания качественных FAQ
Анализирует каждую страницу и извлекает полезную информацию
"""
import os
import json
from database.models import Database
import asyncio


class ManualPageAnalyzer:
    def __init__(self):
        self.pages_dir = "data/fa_pages/text"
        self.analyzed_pages = []
        self.faq_data = []
        self.contacts_data = []

    def get_priority_pages(self):
        """Получить список страниц по приоритету"""
        all_files = os.listdir(self.pages_dir)

        # Приоритет 1: Страницы для студентов
        priority_1 = [f for f in all_files if 'for-students' in f and 'nso' not in f]

        # Приоритет 2: Оплата, стипендии, общежитие
        priority_2 = [f for f in all_files if any(kw in f for kw in ['oplata', 'free', 'stipend', 'dormitory'])]

        # Приоритет 3: ДПО, образование
        priority_3 = [f for f in all_files if any(kw in f for kw in ['dpo', 'education', 'studup'])]

        # Приоритет 4: Трудоустройство
        priority_4 = [f for f in all_files if 'employment' in f]

        # Приоритет 5: Поступление
        priority_5 = [f for f in all_files if 'applicant' in f or 'for-applicants' in f]

        # Остальные
        processed = set(priority_1 + priority_2 + priority_3 + priority_4 + priority_5)
        other = [f for f in all_files if f not in processed]

        return priority_1 + priority_2 + priority_3 + priority_4 + priority_5 + other

    def read_page(self, filename):
        """Прочитать страницу"""
        filepath = os.path.join(self.pages_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def save_progress(self):
        """Сохранить прогресс"""
        with open('data/manual_analysis_progress.json', 'w', encoding='utf-8') as f:
            json.dump({
                'analyzed_pages': self.analyzed_pages,
                'faq_count': len(self.faq_data),
                'contacts_count': len(self.contacts_data),
                'faq': self.faq_data,
                'contacts': self.contacts_data
            }, f, ensure_ascii=False, indent=2)

    async def save_to_database(self, db_path='finguide.db'):
        """Сохранить в базу данных"""
        db = Database(db_path)
        await db.connect()

        saved_faq = 0
        saved_contacts = 0

        for item in self.faq_data:
            try:
                await db.add_faq(
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'Общие вопросы')
                )
                saved_faq += 1
            except Exception:
                pass

        for item in self.contacts_data:
            try:
                await db.add_contact(
                    service_name=item['service_name'],
                    phone=item.get('phone'),
                    email=item.get('email')
                )
                saved_contacts += 1
            except Exception:
                pass

        await db.close()
        print(f"\nSaved to database: {saved_faq} FAQ, {saved_contacts} contacts")

    def start_analysis(self):
        """Начать анализ"""
        pages = self.get_priority_pages()

        print("="*80)
        print("MANUAL PAGE ANALYZER")
        print("="*80)
        print(f"Total pages to analyze: {len(pages)}")
        print(f"Priority pages (for-students): {len([p for p in pages if 'for-students' in p])}")
        print("="*80)
        print("\nReady to analyze pages one by one.")
        print("Each page will be shown for manual analysis.")
        print("="*80)

        return pages


if __name__ == "__main__":
    analyzer = ManualPageAnalyzer()
    pages = analyzer.start_analysis()

    print(f"\nFirst 10 priority pages:")
    for i, page in enumerate(pages[:10], 1):
        print(f"{i}. {page}")
