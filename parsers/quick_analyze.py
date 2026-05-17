"""
Быстрый анализ скачанных страниц и создание FAQ
Без использования Anthropic API - анализ на основе паттернов
"""
import os
import json
import re
from database.models import Database
import asyncio


class QuickFAQAnalyzer:
    def __init__(self):
        self.pages_dir = "data/fa_pages/text"
        self.faq_data = []
        self.contacts_data = []

    def extract_faq_from_text(self, text: str, url: str) -> list:
        """Извлечь FAQ из текста на основе паттернов"""
        faqs = []

        # Паттерн 1: Заголовки с вопросами
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()

            # Ищем вопросы
            if any(q in line.lower() for q in ['как ', 'где ', 'когда ', 'что ', 'почему ', 'можно ли ', 'сколько ']):
                if len(line) > 15 and len(line) < 200 and '?' in line:
                    # Собираем ответ из следующих строк
                    answer_lines = []
                    for j in range(i+1, min(i+10, len(lines))):
                        next_line = lines[j].strip()
                        if len(next_line) > 20:
                            answer_lines.append(next_line)
                        if len(answer_lines) >= 5:
                            break

                    if answer_lines:
                        answer = ' '.join(answer_lines)
                        if len(answer) > 50:
                            faqs.append({
                                'question': line,
                                'answer': answer[:1000],
                                'source_url': url,
                                'category': self.detect_category(line + ' ' + answer)
                            })

        return faqs

    def detect_category(self, text: str) -> str:
        """Определить категорию"""
        text_lower = text.lower()

        categories = {
            'Стипендии и выплаты': ['стипенди', 'выплат', 'деньги', 'оплат', 'скидк'],
            'Общежитие': ['общежити', 'жильё', 'комнат', 'проживан'],
            'Библиотека': ['библиотек', 'книг', 'учебник'],
            'Документы и справки': ['справк', 'документ', 'выписк', 'диплом', 'прейскурант'],
            'Учебный процесс': ['расписан', 'экзамен', 'сесси', 'зачёт', 'пар', 'обучен'],
            'Поступление': ['поступ', 'абитуриент', 'прием', 'вступительн'],
            'Дополнительное образование': ['дпо', 'studup', 'переподготовк', 'повышение квалификации'],
            'Трудоустройство': ['работ', 'карьер', 'стажировк', 'вакан'],
            'Международная деятельность': ['международн', 'обмен', 'зарубеж', 'стипенди', 'грант'],
        }

        for category, keywords in categories.items():
            if any(kw in text_lower for kw in keywords):
                return category

        return 'Общие вопросы'

    def extract_contacts(self, text: str, url: str) -> list:
        """Извлечь контакты"""
        contacts = []

        # Ищем телефоны
        phone_pattern = re.compile(r'\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
        phones = phone_pattern.findall(text)

        # Ищем email
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        emails = email_pattern.findall(text)

        if phones or emails:
            # Пытаемся найти название службы
            lines = text.split('\n')
            service_name = "Контакт"

            for line in lines[:20]:
                if any(word in line.lower() for word in ['деканат', 'отдел', 'служба', 'центр', 'управление']):
                    service_name = line.strip()[:100]
                    break

            if phones or emails:
                contacts.append({
                    'service_name': service_name,
                    'phone': phones[0] if phones else None,
                    'email': emails[0] if emails else None,
                    'source_url': url
                })

        return contacts

    def analyze_all_pages(self):
        """Анализировать все скачанные страницы"""
        print("="*80)
        print("QUICK FAQ ANALYZER")
        print("="*80)

        # Получаем список файлов
        text_files = [f for f in os.listdir(self.pages_dir) if f.endswith('.txt')]
        print(f"Found {len(text_files)} text files")

        # Приоритетные файлы
        priority_keywords = ['for-students', 'oplata', 'free', 'studentu', 'employment', 'library']

        priority_files = [f for f in text_files if any(kw in f for kw in priority_keywords)]
        other_files = [f for f in text_files if f not in priority_files]

        all_files = priority_files + other_files

        print(f"Priority files: {len(priority_files)}")
        print("="*80)

        for i, filename in enumerate(all_files[:100], 1):  # Анализируем первые 100
            filepath = os.path.join(self.pages_dir, filename)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()

                # Извлекаем URL
                url_match = re.search(r'URL: (.+)', text)
                url = url_match.group(1) if url_match else "unknown"

                print(f"[{i}/100] Analyzing: {filename[:60]}...")

                # Извлекаем FAQ
                faqs = self.extract_faq_from_text(text, url)
                self.faq_data.extend(faqs)

                # Извлекаем контакты
                contacts = self.extract_contacts(text, url)
                self.contacts_data.extend(contacts)

                if faqs or contacts:
                    print(f"  Found: {len(faqs)} FAQ, {len(contacts)} contacts")

            except Exception as e:
                print(f"  Error: {e}")

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE!")
        print("="*80)
        print(f"Total FAQ found: {len(self.faq_data)}")
        print(f"Total contacts found: {len(self.contacts_data)}")

        # Группируем по категориям
        categories = {}
        for faq in self.faq_data:
            cat = faq.get('category', 'Без категории')
            categories[cat] = categories.get(cat, 0) + 1

        print("\nFAQ by category:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")

        print("="*80)

    def save_to_json(self, filename='data/quick_analyzed_faq.json'):
        """Сохранить в JSON"""
        data = {
            'faq': self.faq_data,
            'contacts': self.contacts_data,
            'stats': {
                'total_faq': len(self.faq_data),
                'total_contacts': len(self.contacts_data)
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Results saved to: {filename}")

    async def save_to_database(self, db_path='finguide.db'):
        """Сохранить в базу данных"""
        print("\nSaving to database...")
        db = Database(db_path)
        await db.connect()

        saved_faq = 0
        saved_contacts = 0

        # Сохраняем FAQ
        for item in self.faq_data:
            try:
                await db.add_faq(
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'Общие вопросы')
                )
                saved_faq += 1
            except Exception as e:
                pass  # Пропускаем дубликаты

        # Сохраняем контакты
        for item in self.contacts_data:
            try:
                await db.add_contact(
                    service_name=item['service_name'],
                    phone=item.get('phone'),
                    email=item.get('email')
                )
                saved_contacts += 1
            except Exception as e:
                pass

        await db.close()
        print(f"Saved to database: {saved_faq} FAQ, {saved_contacts} contacts")


async def main():
    analyzer = QuickFAQAnalyzer()
    analyzer.analyze_all_pages()
    analyzer.save_to_json()

    print("\nSave to database? (y/n)")
    response = input().strip().lower()
    if response == 'y':
        await analyzer.save_to_database()


if __name__ == "__main__":
    asyncio.run(main())
