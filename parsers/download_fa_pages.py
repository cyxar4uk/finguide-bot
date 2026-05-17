"""
Этап 1: Скачивание всех страниц FA.RU в текстовые файлы
Сохраняет HTML и текст каждой страницы для последующего анализа
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import hashlib
from typing import Set
import json


class FAPageDownloader:
    def __init__(self):
        self.base_url = "https://www.fa.ru"
        self.visited_urls: Set[str] = set()
        self.max_pages = 10000
        self.session = None
        self.output_dir = "data/fa_pages"

        # Создаём директории
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/html", exist_ok=True)
        os.makedirs(f"{self.output_dir}/text", exist_ok=True)

        # Загружаем уже скачанные URL
        self.load_existing_urls()

        # Приоритетные разделы
        self.priority_sections = [
            "/for-students/",       # ПРИОРИТЕТ 1 - для студентов
            "/studentu/",
            "/for-students/free/",
            "/for-students/oplata/",
            "/for-students/student-science/",
            "/abiturientu/",
            "/contacts/",
            "/about/",
            "/education/",
            "/science/",
            "/international/",
            "/news/",
            "/structure/",
            "/admission/",
            "/library/",
            "/dormitory/",
            "/schedule/",
            "/departments/",
            "/faculties/",
        ]

        self.pages_data = []
        self.recursion_depth = 0
        self.max_recursion_depth = 20  # Увеличена глубина для /for-students/

    async def init_session(self):
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def close_session(self):
        if self.session:
            await self.session.close()

    def load_existing_urls(self):
        """Загрузить уже скачанные URL из индекса"""
        index_path = f"{self.output_dir}/index.json"
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.visited_urls = set(data.get('visited_urls', []))
                    self.pages_data = data.get('pages', [])
                    print(f"Loaded {len(self.visited_urls)} already downloaded URLs")
            except Exception as e:
                print(f"Could not load existing index: {e}")

    def get_filename(self, url: str) -> str:
        """Генерирует безопасное имя файла из URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        path = urlparse(url).path.strip('/').replace('/', '_')

        # Ограничиваем длину имени файла
        if len(path) > 100:
            path = path[:100]

        if not path:
            path = 'index'
        return f"{path}_{url_hash}"

    async def fetch_page(self, url: str) -> tuple:
        """Получить HTML и текст страницы"""
        try:
            async with self.session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    return html, response.status
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None, None

    def extract_text(self, html: str) -> str:
        """Извлечь чистый текст из HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        # Удаляем скрипты и стили
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Получаем текст
        text = soup.get_text(separator='\n', strip=True)

        # Очищаем множественные переносы строк
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def extract_links(self, html: str, current_url: str) -> list:
        """Извлечь все ссылки со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(current_url, href)

            # Фильтруем только внутренние ссылки
            parsed = urlparse(full_url)
            if parsed.netloc in ['www.fa.ru', 'fa.ru']:
                # Убираем якоря и параметры
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                # Пропускаем повторяющиеся паттерны (защита от бесконечной рекурсии)
                if '/for-students/student-science/nso/' in clean_url:
                    # Считаем количество повторений
                    count = clean_url.count('/for-students/student-science/nso/')
                    if count > 1:
                        continue  # Пропускаем

                if clean_url not in self.visited_urls:
                    links.append(clean_url)

        return links

    async def download_page(self, url: str, depth: int = 0):
        """Скачать и сохранить страницу"""
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
            return

        # Защита от слишком глубокой рекурсии
        if depth > self.max_recursion_depth:
            return

        print(f"[{len(self.visited_urls)+1}/{self.max_pages}] Downloading: {url}")
        self.visited_urls.add(url)

        html, status = await self.fetch_page(url)
        if not html:
            return

        # Извлекаем текст
        text = self.extract_text(html)

        # Генерируем имя файла
        filename = self.get_filename(url)

        # Сохраняем HTML
        html_path = f"{self.output_dir}/html/{filename}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # Сохраняем текст
        text_path = f"{self.output_dir}/text/{filename}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"{'='*80}\n\n")
            f.write(text)

        # Сохраняем метаданные
        self.pages_data.append({
            'url': url,
            'filename': filename,
            'html_path': html_path,
            'text_path': text_path,
            'text_length': len(text),
            'status': status
        })

        # Получаем новые ссылки
        links = self.extract_links(html, url)

        # Парсим приоритетные ссылки
        priority_links = [l for l in links if any(p in l for p in self.priority_sections)]
        other_links = [l for l in links if l not in priority_links]

        # Сначала приоритетные
        for link in priority_links[:10]:
            await self.download_page(link, depth + 1)

        # Потом остальные
        for link in other_links[:5]:
            await self.download_page(link, depth + 1)

    async def start_downloading(self):
        """Запуск скачивания"""
        print("="*80)
        print("FA.RU PAGE DOWNLOADER")
        print("="*80)
        print(f"Max pages: {self.max_pages}")
        print(f"Output directory: {self.output_dir}")
        print("="*80)

        await self.init_session()

        try:
            # Начинаем с главной и приоритетных разделов
            start_urls = [self.base_url] + [self.base_url + section for section in self.priority_sections]

            for url in start_urls:
                await self.download_page(url)

            print(f"\n{'='*80}")
            print("DOWNLOAD COMPLETE!")
            print(f"{'='*80}")
            print(f"Total pages downloaded: {len(self.visited_urls)}")
            print(f"HTML files: {self.output_dir}/html/")
            print(f"Text files: {self.output_dir}/text/")

        finally:
            await self.close_session()

        # Сохраняем индекс
        index_path = f"{self.output_dir}/index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_pages': len(self.visited_urls),
                'pages': self.pages_data,
                'visited_urls': list(self.visited_urls)
            }, f, ensure_ascii=False, indent=2)

        print(f"Index saved: {index_path}")
        print("="*80)


async def main():
    downloader = FAPageDownloader()
    # max_pages установлен в __init__ = 10000

    await downloader.start_downloading()


if __name__ == "__main__":
    asyncio.run(main())
