"""
Парсер сайта Финансового университета (fa.ru)
Собирает FAQ, контакты, информацию для студентов
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import Set, List, Dict
import json
from database.models import Database


class FAParser:
    def __init__(self):
        self.base_url = "https://www.fa.ru"
        self.visited_urls: Set[str] = set()
        self.max_pages = 100  # Лимит страниц для парсинга
        self.session = None

        # Приоритетные разделы для парсинга
        self.priority_sections = [
            "/studentu/",           # Для студентов
            "/abiturientu/",        # Для абитуриентов
            "/contacts/",           # Контакты
            "/about/",              # О университете
            "/education/",          # Образование
            "/science/",            # Наука
            "/international/",      # Международное сотрудничество
            "/news/",               # Новости
            "/structure/",          # Структура
            "/admission/",          # Поступление
            "/library/",            # Библиотека
            "/dormitory/",          # Общежитие
            "/schedule/",           # Расписание
            "/departments/",        # Кафедры
            "/faculties/",          # Факультеты
        ]

        self.faq_data = []
        self.contacts_data = []

    async def init_session(self):
        """Инициализация HTTP сессии"""
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def close_session(self):
        """Закрытие сессии"""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> str:
        """Получить HTML страницы"""
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return ""

    def is_valid_url(self, url: str) -> bool:
        """Проверка, что URL относится к fa.ru"""
        parsed = urlparse(url)
        return parsed.netloc in ['www.fa.ru', 'fa.ru']

    def extract_links(self, html: str, current_url: str) -> List[str]:
        """Извлечь все ссылки со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)

            # Фильтруем только внутренние ссылки
            if self.is_valid_url(full_url) and full_url not in self.visited_urls:
                # Убираем якоря и параметры
                clean_url = full_url.split('#')[0].split('?')[0]
                links.append(clean_url)

        return links

    def extract_faq(self, html: str, url: str) -> List[Dict]:
        """Извлечь FAQ со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        faq_items = []

        # Ищем различные паттерны FAQ
        # Паттерн 1: <h3>Вопрос</h3><p>Ответ</p>
        headings = soup.find_all(['h2', 'h3', 'h4'])
        for heading in headings:
            question_text = heading.get_text(strip=True)

            # Проверяем, что это похоже на вопрос
            if any(q in question_text.lower() for q in ['как', 'где', 'когда', 'что', 'почему', 'можно ли']):
                # Ищем ответ в следующих элементах
                answer_parts = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4']:
                        break
                    if sibling.name in ['p', 'div', 'ul', 'ol']:
                        answer_parts.append(sibling.get_text(strip=True))

                if answer_parts:
                    answer = '\n'.join(answer_parts[:3])  # Берём первые 3 параграфа
                    if len(answer) > 50:  # Минимальная длина ответа
                        faq_items.append({
                            'question': question_text,
                            'answer': answer[:1000],  # Ограничиваем длину
                            'source_url': url,
                            'category': self.detect_category(question_text, answer)
                        })

        # Паттерн 2: Аккордеоны и FAQ блоки
        faq_blocks = soup.find_all(['div', 'section'], class_=re.compile(r'faq|accordion|question', re.I))
        for block in faq_blocks:
            question = block.find(['h3', 'h4', 'dt', 'summary'])
            answer = block.find(['p', 'dd', 'div'], class_=re.compile(r'answer|content', re.I))

            if question and answer:
                faq_items.append({
                    'question': question.get_text(strip=True),
                    'answer': answer.get_text(strip=True)[:1000],
                    'source_url': url,
                    'category': self.detect_category(question.get_text(), answer.get_text())
                })

        return faq_items

    def extract_contacts(self, html: str, url: str) -> List[Dict]:
        """Извлечь контакты со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        contacts = []

        # Ищем телефоны
        phone_pattern = re.compile(r'\+?[78][\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
        # Ищем email
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        # Ищем блоки с контактами
        contact_blocks = soup.find_all(['div', 'section'], class_=re.compile(r'contact|address', re.I))

        for block in contact_blocks:
            text = block.get_text()

            phones = phone_pattern.findall(text)
            emails = email_pattern.findall(text)

            # Пытаемся найти название службы
            service_name = block.find(['h2', 'h3', 'h4'])
            if service_name:
                service_name = service_name.get_text(strip=True)
            else:
                service_name = "Контакт"

            if phones or emails:
                contacts.append({
                    'service_name': service_name,
                    'phone': phones[0] if phones else None,
                    'email': emails[0] if emails else None,
                    'source_url': url,
                    'description': text[:200]
                })

        return contacts

    def detect_category(self, question: str, answer: str) -> str:
        """Определить категорию FAQ"""
        text = (question + " " + answer).lower()

        categories = {
            'Стипендии': ['стипенди', 'выплат', 'деньги', 'оплат'],
            'Общежитие': ['общежити', 'жильё', 'комнат', 'проживан'],
            'Библиотека': ['библиотек', 'книг', 'учебник'],
            'Документы': ['справк', 'документ', 'выписк', 'диплом'],
            'Учебный процесс': ['расписан', 'экзамен', 'сесси', 'зачёт', 'пар'],
            'Поступление': ['поступ', 'абитуриент', 'прием', 'вступительн'],
            'Контакты': ['телефон', 'email', 'адрес', 'контакт'],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return 'Общие вопросы'

    async def parse_page(self, url: str):
        """Парсинг одной страницы"""
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
            return

        print(f"Parsing: {url}")
        self.visited_urls.add(url)

        html = await self.fetch_page(url)
        if not html:
            return

        # Извлекаем данные
        faq = self.extract_faq(html, url)
        contacts = self.extract_contacts(html, url)

        self.faq_data.extend(faq)
        self.contacts_data.extend(contacts)

        print(f"  Found: {len(faq)} FAQ, {len(contacts)} contacts")

        # Получаем новые ссылки
        links = self.extract_links(html, url)

        # Парсим приоритетные ссылки
        priority_links = [l for l in links if any(p in l for p in self.priority_sections)]
        other_links = [l for l in links if l not in priority_links]

        # Сначала парсим приоритетные
        for link in priority_links[:5]:  # Ограничиваем количество
            await self.parse_page(link)

    async def start_parsing(self):
        """Запуск парсинга"""
        print("Starting FA.RU parser...")
        print(f"Max pages: {self.max_pages}")

        await self.init_session()

        try:
            # Начинаем с главной и приоритетных разделов
            start_urls = [self.base_url] + [self.base_url + section for section in self.priority_sections]

            for url in start_urls:
                await self.parse_page(url)

            print(f"\nParsing complete!")
            print(f"Total pages visited: {len(self.visited_urls)}")
            print(f"Total FAQ found: {len(self.faq_data)}")
            print(f"Total contacts found: {len(self.contacts_data)}")

        finally:
            await self.close_session()

    async def save_to_database(self, db_path: str = 'finguide.db'):
        """Сохранить данные в базу"""
        db = Database(db_path)
        await db.connect()

        print("\nSaving to database...")

        # Сохраняем FAQ
        for item in self.faq_data:
            try:
                await db.add_faq(
                    question=item['question'],
                    answer=item['answer'],
                    category=item.get('category', 'Общие вопросы')
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
                    description=item.get('description')
                )
            except Exception as e:
                print(f"Error saving contact: {e}")

        await db.close()
        print("Data saved to database!")

    def save_to_json(self, filename: str = 'parsed_data.json'):
        """Сохранить данные в JSON"""
        data = {
            'faq': self.faq_data,
            'contacts': self.contacts_data,
            'stats': {
                'pages_visited': len(self.visited_urls),
                'faq_count': len(self.faq_data),
                'contacts_count': len(self.contacts_data)
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Data saved to {filename}")


async def main():
    parser = FAParser()

    # Настройки парсинга
    parser.max_pages = 50  # Можно увеличить для более глубокого парсинга

    # Запускаем парсинг
    await parser.start_parsing()

    # Сохраняем результаты
    parser.save_to_json('data/fa_parsed_data.json')
    await parser.save_to_database()


if __name__ == "__main__":
    print("FA.RU Parser v1.0")
    print("="*60)
    asyncio.run(main())
