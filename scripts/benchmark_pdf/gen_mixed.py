import os
import random
import time
from pathlib import Path
import subprocess
import sys
import re
import base64
from typing import List, Optional

# Проверяем Playwright
try:
    from playwright.sync_api import sync_playwright, ViewportSize, PdfMargins
except ImportError:
    print("Устанавливаем Playwright...")
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    from playwright.sync_api import sync_playwright, ViewportSize, PdfMargins


class LocalTextGenerator:
    """Генератор текстовых блоков из локальных txt файлов"""

    def __init__(self, text_dir="texts"):
        self.text_dir = Path(text_dir)
        self.text_files = []
        self.texts_by_length = {
            'short': [],
            'medium': [],
            'long': [],
            'very_long': []
        }
        self._load_texts()

    def _load_texts(self):
        """Загружает все текстовые файлы из директории и поддиректорий"""
        if not self.text_dir.exists():
            print(f"⚠️ Директория {self.text_dir} не найдена!")
            return

        self.text_files = list(self.text_dir.rglob("*.txt"))

        if not self.text_files:
            print(f"⚠️ В директории {self.text_dir} не найдено .txt файлов!")
            return

        print(f"📂 Найдено {len(self.text_files)} текстовых файлов")

        for txt_file in self.text_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    continue

                word_count = len(content.split())

                if word_count < 50:
                    self.texts_by_length['short'].append(content)
                elif word_count < 200:
                    self.texts_by_length['medium'].append(content)
                elif word_count < 500:
                    self.texts_by_length['long'].append(content)
                else:
                    self.texts_by_length['very_long'].append(content)

            except Exception as e:
                print(f"  ❌ Ошибка чтения {txt_file.name}: {e}")

        print(f"📊 Статистика текстов:")
        for length_type, texts in self.texts_by_length.items():
            print(f"  {length_type}: {len(texts)} файлов")

        total_texts = sum(len(texts) for texts in self.texts_by_length.values())
        if total_texts == 0:
            print("❌ Нет загруженных текстов!")

    def get_text_by_length(self, length_type='medium'):
        """Возвращает случайный текст из категории"""
        texts = self.texts_by_length.get(length_type, [])

        if not texts:
            all_texts = []
            for category in self.texts_by_length.values():
                all_texts.extend(category)
            if all_texts:
                return random.choice(all_texts)
            return None

        return random.choice(texts)

    def split_into_paragraphs(self, text, num_paragraphs=None):
        """Разбивает текст на параграфы"""
        sentences = re.split(r'(?<=[.!?])\s+', text)

        if len(sentences) < 3 or (num_paragraphs is None and random.random() < 0.4):
            return [text]

        if num_paragraphs is None:
            num_paragraphs = random.randint(2, min(5, len(sentences)))

        paragraphs = []
        sentences_per_paragraph = max(1, len(sentences) // num_paragraphs)

        for i in range(num_paragraphs):
            start = i * sentences_per_paragraph
            end = min(start + sentences_per_paragraph, len(sentences))
            if start < len(sentences):
                paragraph = ' '.join(sentences[start:end])
                paragraphs.append(paragraph)

        return paragraphs

    def generate_random_font_style(self):
        """Генерирует случайный стиль шрифта"""
        fonts = [
            'Georgia, serif',
            'Times New Roman, serif',
            'Arial, sans-serif',
            'Helvetica, sans-serif',
            'Verdana, sans-serif',
            'Tahoma, sans-serif',
            'Trebuchet MS, sans-serif',
            'Garamond, serif',
            'Palatino Linotype, serif',
            'Courier New, monospace'
        ]
        return random.choice(fonts)

    def generate_random_text_style(self):
        """Генерирует случайные стили для текста"""
        styles = []

        font_size = random.randint(9, 16)
        styles.append(f"font-size: {font_size}px;")

        line_height = random.choice(['1.3', '1.4', '1.5', '1.6', '1.8', '2.0'])
        styles.append(f"line-height: {line_height};")

        if random.random() > 0.7:
            styles.append("font-weight: bold;")
        if random.random() > 0.85:
            styles.append("font-style: italic;")
        if random.random() > 0.9:
            styles.append("text-decoration: underline;")
        if random.random() > 0.95:
            styles.append("text-transform: uppercase;")

        if random.random() > 0.85:
            colors = ['#2c3e50', '#34495e', '#1a1a1a', '#4a4a4a', '#2d3436']
            styles.append(f"color: {random.choice(colors)};")

        if random.random() > 0.92:
            bg_colors = ['#fef9e7', '#f0f8ff', '#f5f5f5', '#faf3e0', '#e8f4f8']
            styles.append(f"background-color: {random.choice(bg_colors)}; padding: 4px 8px; border-radius: 4px;")

        if random.random() > 0.6:
            margin_top = random.choice(['0', '2', '4', '6', '8', '10'])
            styles.append(f"margin-top: {margin_top}px;")

        if random.random() > 0.5:
            margin_bottom = random.choice(['0', '2', '4', '6', '8'])
            styles.append(f"margin-bottom: {margin_bottom}px;")

        if random.random() > 0.7:
            text_indent = random.choice(['10', '15', '20', '25', '30'])
            styles.append(f"text-indent: {text_indent}px;")

        align = random.choice(['left', 'justify', 'center', 'right'])
        styles.append(f"text-align: {align};")

        if random.random() > 0.8:
            letter_spacing = random.choice(['0.5', '0.8', '1', '1.2', '1.5'])
            styles.append(f"letter-spacing: {letter_spacing}px;")

        return ' '.join(styles)

    def generate_text_block(self, length_type=None):
        """Генерирует текстовый блок"""
        # Если длина не указана, выбираем случайно между short и medium
        if length_type is None:
            length_type = random.choice(['short', 'medium'])

        text = self.get_text_by_length(length_type)

        if text is None:
            return "<p>Текст не найден</p>"

        words = text.split()
        total_words = len(words)

        if length_type == 'short':
            target_words = random.randint(10, 30)
        elif length_type == 'medium':
            target_words = random.randint(50, 150)
        elif length_type == 'long':
            target_words = random.randint(200, 500)
        else:
            target_words = random.randint(600, 1500)

        if total_words <= target_words:
            final_text = text
        else:
            start = random.randint(0, max(0, total_words - target_words))
            final_text = ' '.join(words[start:start + target_words])

        add_paragraphs = random.random() < 0.6

        if add_paragraphs and len(final_text) > 100:
            paragraphs = self.split_into_paragraphs(final_text)
        else:
            paragraphs = [final_text]

        # Добавляем заголовок
        title = "Текст"
        if self.text_files:
            random_file = random.choice(self.text_files)
            title = random_file.stem.replace('_', ' ').title()

        if random.random() > 0.3:
            title_prefixes = ['Введение в', 'Обзор', 'Анализ', 'Исследование', 'Основы']
            title = f"{random.choice(title_prefixes)}: {title}"

        font_family = self.generate_random_font_style()

        formatted_paragraphs = []
        for i, paragraph in enumerate(paragraphs):
            style = self.generate_random_text_style()
            if i == 0:
                style = re.sub(r'margin-top: \d+px;', 'margin-top: 0;', style)
            formatted_paragraphs.append(f"<p style='{style}'>{paragraph}</p>")

        title_style = f"font-family: {font_family}; font-size: {random.randint(14, 18)}px;"
        title_style += f" font-weight: {random.choice(['bold', 'normal'])};"
        if random.random() > 0.7:
            title_style += f" color: {random.choice(['#2c3e50', '#2980b9', '#1a5276'])};"
        if random.random() > 0.8:
            title_style += " text-decoration: underline;"

        block_style = f"font-family: {font_family};"

        formatted_text = f"<div style='{block_style}'>"
        formatted_text += f"<h3 style='{title_style}; margin-bottom: 8px;'>{title}</h3>\n"
        formatted_text += '\n'.join(formatted_paragraphs)
        formatted_text += "</div>"

        return formatted_text


class ImageHandler:
    """Обработчик изображений"""

    def __init__(self, images_dir="images"):
        self.images_dir = Path(images_dir)
        self.image_files = []
        self._load_images()

    def _load_images(self):
        """Загружает все изображения из директории и поддиректорий"""
        if not self.images_dir.exists():
            print(f"⚠️ Директория {self.images_dir} не найдена!")
            return

        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}
        self.image_files = []

        for ext in image_extensions:
            self.image_files.extend(self.images_dir.rglob(f"*{ext}"))
            self.image_files.extend(self.images_dir.rglob(f"*{ext.upper()}"))

        self.image_files = sorted(set(self.image_files))

        if not self.image_files:
            print(f"⚠️ В директории {self.images_dir} не найдено изображений!")
        else:
            print(f"📂 Найдено {len(self.image_files)} изображений")

    def get_random_image(self):
        """Возвращает случайное изображение"""
        if not self.image_files:
            return None
        return random.choice(self.image_files)

    def image_to_base64(self, image_path):
        """Конвертирует изображение в base64"""
        try:
            with open(image_path, 'rb') as f:
                img_data = f.read()

            suffix = image_path.suffix.lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(suffix, 'image/png')

            base64_data = base64.b64encode(img_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            print(f"  Ошибка при конвертации {image_path.name}: {e}")
            return None


class TableGenerator:
    """Генератор HTML-таблиц"""

    def __init__(self):
        self.texts = [
            'Данные', 'Значение', 'Показатель', 'Результат', 'Процесс',
            'Система', 'Функция', 'Параметр', 'Алгоритм', 'Метод',
            'Анализ', 'Отчет', 'Статистика', 'Выборка', 'Интервал',
            'Коэффициент', 'Индекс', 'Погрешность', 'Отклонение', 'Среднее'
        ]

    def get_random_value(self):
        """Генерирует случайное значение для ячейки"""
        cell_type = random.choice(['text', 'number', 'date'])
        if cell_type == 'text':
            return random.choice(self.texts)
        elif cell_type == 'number':
            return str(random.randint(1, 9999))
        else:
            return f"{random.randint(1, 28):02d}.{random.randint(1, 12):02d}.{random.randint(2020, 2025)}"

    def generate_table(self):
        """Генерирует HTML-таблицу"""
        rows = random.randint(4, 8)
        cols = random.randint(3, 5)

        html = [
            '<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 10px; border: 1px solid #333;">']

        # Заголовок
        html.append('<thead>')
        html.append('<tr>')
        for c in range(cols):
            bg_color = '#e8f4f8' if random.random() > 0.3 else '#f0f0f0'
            html.append(
                f'<th style="border: 1px solid #333; padding: 6px; text-align: center; background-color: {bg_color}; font-weight: bold;">Заголовок {c + 1}</th>')
        html.append('</tr>')
        html.append('</thead>')

        # Тело таблицы
        html.append('<tbody>')
        for r in range(rows):
            html.append('<tr>')
            for c in range(cols):
                bg_color = '#f9f9f9' if r % 2 == 0 else 'white'
                html.append(
                    f'<td style="border: 1px solid #333; padding: 4px 6px; text-align: center; background-color: {bg_color};">{self.get_random_value()}</td>')
            html.append('</tr>')
        html.append('</tbody>')
        html.append('</table>')

        return '\n'.join(html)


class CombinedPDFGenerator:
    """Генератор PDF с комбинацией изображений, таблиц и текста"""

    def __init__(self, images_dir="images", text_dir="texts", output_dir="generated_pdfs_combined"):
        self.images_dir = Path(images_dir)
        self.text_dir = Path(text_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp_html_combined")
        self.temp_dir.mkdir(exist_ok=True)

        self.image_handler = ImageHandler(images_dir)
        self.text_generator = LocalTextGenerator(text_dir)
        self.table_generator = TableGenerator()

    def create_html_page(self, elements):
        """
        Создает HTML-страницу с элементами в случайном порядке
        elements: список словарей с элементами {'type': 'image'/'table'/'text', 'content': ...}
        """
        if not elements:
            return '<div>Нет элементов</div>'

        # Перемешиваем элементы
        random.shuffle(elements)

        # Строим HTML для каждого элемента
        elements_html = []
        for element in elements:
            if element['type'] == 'image':
                # Изображение с подписью
                caption = random.choice(['Рис. 1', 'Иллюстрация', 'Схема', 'Диаграмма', 'Изображение'])
                elements_html.append(f'''
                <div style="margin: 5px 0; text-align: center;">
                    <img src="{element['content']}" style="max-width: 100%; max-height: 300px; object-fit: contain; border: 1px solid #e0e0e0; border-radius: 4px;" />
                    <div style="font-size: 10px; color: #666; margin-top: 4px; font-style: italic;">{caption}</div>
                </div>
                ''')

            elif element['type'] == 'table':
                # Таблица с заголовком
                elements_html.append(f'''
                <div style="margin: 5px 0;">
                    <div style="font-size: 11px; font-weight: bold; margin-bottom: 4px;">Таблица</div>
                    {element['content']}
                </div>
                ''')

            elif element['type'] == 'text':
                # Текстовый блок
                elements_html.append(f'''
                <div style="margin: 5px 0;">
                    {element['content']}
                </div>
                ''')

        # Собираем страницу
        content = ''.join(elements_html)

        # Случайные отступы для страницы
        padding = random.choice(['10', '15', '20'])

        return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ 
        margin: 0; 
        padding: 0; 
        background: white; 
        font-family: 'Georgia', serif; 
        height: 100vh; 
        width: 100vw; 
        display: flex; 
        align-items: flex-start; 
        justify-content: center; 
    }}
    .page-container {{ 
        width: 100%; 
        height: 100%; 
        max-width: 1200px; 
        max-height: 800px; 
        padding: {padding}px; 
        display: flex; 
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        overflow: hidden;
    }}
    h3 {{ margin: 0 0 8px 0; }}
    p {{ margin: 0; }}
    @media print {{ 
        body {{ margin: 0; padding: 0; }} 
        .page-container {{ max-width: 100%; max-height: 100%; padding: 10px; }} 
    }}
</style>
</head>
<body><div class="page-container">{content}</div></body>
</html>'''

    def generate_page_elements(self):
        """
        Генерирует элементы для страницы (1 изображение, 1 таблица, 1-2 текстовых блока)
        Возвращает список элементов
        """
        elements = []

        # Добавляем изображение
        image_path = self.image_handler.get_random_image()
        if image_path:
            img_base64 = self.image_handler.image_to_base64(image_path)
            if img_base64:
                elements.append({
                    'type': 'image',
                    'content': img_base64
                })
        else:
            # Если нет изображений, добавляем заглушку
            elements.append({
                'type': 'text',
                'content': '<p style="color: #999; text-align: center;">Изображение не найдено</p>'
            })

        # Добавляем таблицу
        table_html = self.table_generator.generate_table()
        elements.append({
            'type': 'table',
            'content': table_html
        })

        # Добавляем 1-2 текстовых блока (случайная длина short/medium)
        num_texts = random.choice([1, 2])
        for _ in range(num_texts):
            text_block = self.text_generator.generate_text_block()  # без параметра - случайный выбор
            elements.append({
                'type': 'text',
                'content': text_block
            })

        return elements

    def generate_pdf_with_playwright(self, html_pages, pdf_path):
        """Генерирует PDF через Playwright"""
        try:
            full_html = '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { margin: 0; padding: 0; background: white; }
    .page { 
        width: 210mm; 
        height: 297mm; 
        padding: 10mm; 
        margin: 0; 
        page-break-after: always; 
        display: flex; 
        align-items: flex-start; 
        justify-content: center; 
        box-sizing: border-box; 
        background: white;
        overflow: hidden;
    }
    .page-content { 
        width: 100%; 
        height: 100%; 
        display: flex; 
        align-items: flex-start; 
        justify-content: center;
        overflow: hidden;
    }
    @media print { 
        .page { 
            page-break-after: always; 
            margin: 0; 
            padding: 8mm; 
            width: 210mm; 
            height: 297mm;
            overflow: hidden;
        } 
    }
</style></head><body>'''

            for page_html in html_pages:
                start = page_html.find('<body>') + 6
                end = page_html.find('</body>')
                body_content = page_html[start:end] if start != -1 and end != -1 else page_html
                full_html += f'<div class="page"><div class="page-content">{body_content}</div></div>'

            full_html += '</body></html>'

            temp_html = self.temp_dir / f"temp_{hash(pdf_path)}.html"
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(full_html)

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                viewport = ViewportSize(width=1920, height=1080)
                page = browser.new_page(viewport=viewport)

                page.goto(f'file://{temp_html.absolute()}')
                page.wait_for_load_state('networkidle')
                time.sleep(0.3)

                margins = PdfMargins(
                    top="8mm",
                    right="8mm",
                    bottom="8mm",
                    left="8mm"
                )

                page.pdf(
                    path=str(pdf_path),
                    format='A4',
                    print_background=True,
                    margin=margins
                )

                browser.close()

            if temp_html.exists():
                temp_html.unlink()
            return True

        except Exception as e:
            print(f"  ❌ Ошибка при генерации PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_documents(self, num_docs=30, pages_per_doc=100):
        """
        Генерирует документы
        num_docs: количество документов
        pages_per_doc: количество страниц в документе
        """
        print(f"\n📁 Генерация {num_docs} документов по {pages_per_doc} страниц")
        print(f"  На каждой странице: 1 изображение, 1 таблица, 1-2 текстовых блока")
        print(f"  Длина текста: случайно (short или medium)")

        doc_dir = self.output_dir / "documents"
        doc_dir.mkdir(exist_ok=True)

        for doc_num in range(1, num_docs + 1):
            print(f"  📄 Документ {doc_num}/{num_docs}...")
            all_pages = []

            for page_num in range(pages_per_doc):
                # Генерируем элементы для страницы
                elements = self.generate_page_elements()
                page_html = self.create_html_page(elements)
                all_pages.append(page_html)

            # Сохраняем PDF
            pdf_path = doc_dir / f"doc_{doc_num:03d}.pdf"
            success = self.generate_pdf_with_playwright(all_pages, pdf_path)

            if success:
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"    ✅ Создан ({size_mb:.2f} MB)")
            else:
                print(f"    ❌ Ошибка при создании документа {doc_num}")


def main():
    # Параметры
    images_directory = "images"
    text_directory = "texts"
    output_directory = "generated_pdfs_combined"

    # Проверяем наличие директорий
    if not Path(images_directory).exists():
        print(f"❌ Директория '{images_directory}' не найдена!")
        print(f"Создайте папку '{images_directory}' и поместите в нее изображения.")
        print(f"Поддерживаются: PNG, JPG, JPEG, BMP, TIFF, GIF, WebP")
        return

    if not Path(text_directory).exists():
        print(f"❌ Директория '{text_directory}' не найдена!")
        print(f"Создайте папку '{text_directory}' и поместите в нее .txt файлы.")
        return

    # Проверяем наличие файлов
    image_files = list(Path(images_directory).rglob("*"))
    image_files = [f for f in image_files if f.suffix.lower() in {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}]
    if not image_files:
        print(f"❌ В директории '{images_directory}' нет изображений!")
        return

    txt_files = list(Path(text_directory).rglob("*.txt"))
    if not txt_files:
        print(f"❌ В директории '{text_directory}' нет .txt файлов!")
        return

    # Очищаем временные файлы
    temp_dir = Path("temp_html_combined")
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    # Создаем генератор и запускаем
    generator = CombinedPDFGenerator(images_directory, text_directory, output_directory)
    generator.generate_documents(num_docs=30, pages_per_doc=100)

    # Выводим статистику
    total_docs = 30
    total_pages = total_docs * 100

    print("\n📊 СТАТИСТИКА:")
    print(f"  📁 Всего документов: {total_docs}")
    print(f"  📄 Всего страниц: {total_pages}")
    print(f"  📁 Выходная директория: {output_directory}")
    print(f"  📂 Папка с изображениями: {images_directory}")
    print(f"  📂 Папка с текстами: {text_directory}")

    # Проверяем размер
    output_dir = Path(output_directory)
    if output_dir.exists():
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*.pdf")) / (1024 * 1024)
        print(f"  💾 Общий размер: {total_size:.2f} MB")

    print("\n📁 Структура выходных файлов:")
    print(f"  {output_directory}/")
    print("  └── documents/")
    print("      ├── doc_001.pdf")
    print("      ├── doc_002.pdf")
    print("      └── ... (30 документов)")


if __name__ == "__main__":
    main()
