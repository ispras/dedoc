import random
import re
import subprocess
import sys
import time
from pathlib import Path

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

        # Рекурсивно ищем все .txt файлы
        self.text_files = list(self.text_dir.rglob("*.txt"))

        if not self.text_files:
            print(f"⚠️ В директории {self.text_dir} не найдено .txt файлов!")
            return

        print(f"📂 Найдено {len(self.text_files)} текстовых файлов")

        # Загружаем и классифицируем тексты
        for txt_file in self.text_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    continue

                # Определяем длину текста по количеству слов
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

        # Выводим статистику
        print(f"📊 Статистика текстов:")
        for length_type, texts in self.texts_by_length.items():
            print(f"  {length_type}: {len(texts)} файлов")

        # Проверяем, что есть хоть какие-то тексты
        total_texts = sum(len(texts) for texts in self.texts_by_length.values())
        if total_texts == 0:
            print("❌ Нет загруженных текстов! Проверьте директорию с файлами.")

    def get_text_by_length(self, length_type='medium'):
        """Возвращает случайный текст из категории"""
        texts = self.texts_by_length.get(length_type, [])

        # Если в категории нет текстов, берем из любой другой
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
        # Разбиваем по точкам, вопросительным и восклицательным знакам
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Если предложений мало или не хотим параграфы
        if len(sentences) < 3 or (num_paragraphs is None and random.random() < 0.4):
            return [text]

        # Определяем количество параграфов
        if num_paragraphs is None:
            num_paragraphs = random.randint(2, min(5, len(sentences)))

        # Распределяем предложения по параграфам
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

        # Случайный размер шрифта (от 9 до 16)
        font_size = random.randint(9, 16)
        styles.append(f"font-size: {font_size}px;")

        # Случайная высота строки
        line_height = random.choice(['1.3', '1.4', '1.5', '1.6', '1.8', '2.0'])
        styles.append(f"line-height: {line_height};")

        # Случайное начертание
        if random.random() > 0.7:
            styles.append("font-weight: bold;")
        if random.random() > 0.85:
            styles.append("font-style: italic;")
        if random.random() > 0.9:
            styles.append("text-decoration: underline;")
        if random.random() > 0.95:
            styles.append("text-transform: uppercase;")

        # Случайный цвет текста
        if random.random() > 0.85:
            colors = ['#2c3e50', '#34495e', '#1a1a1a', '#4a4a4a', '#2d3436']
            styles.append(f"color: {random.choice(colors)};")

        # Случайный цвет фона для выделения
        if random.random() > 0.92:
            bg_colors = ['#fef9e7', '#f0f8ff', '#f5f5f5', '#faf3e0', '#e8f4f8']
            styles.append(f"background-color: {random.choice(bg_colors)}; padding: 4px 8px; border-radius: 4px;")

        # Случайные отступы
        if random.random() > 0.6:
            margin_top = random.choice(['0', '2', '4', '6', '8', '10'])
            styles.append(f"margin-top: {margin_top}px;")

        if random.random() > 0.5:
            margin_bottom = random.choice(['0', '2', '4', '6', '8'])
            styles.append(f"margin-bottom: {margin_bottom}px;")

        # Случайный отступ первой строки
        if random.random() > 0.7:
            text_indent = random.choice(['10', '15', '20', '25', '30'])
            styles.append(f"text-indent: {text_indent}px;")

        # Случайное выравнивание
        align = random.choice(['left', 'justify', 'center', 'right'])
        styles.append(f"text-align: {align};")

        # Случайные межбуквенные интервалы
        if random.random() > 0.8:
            letter_spacing = random.choice(['0.5', '0.8', '1', '1.2', '1.5'])
            styles.append(f"letter-spacing: {letter_spacing}px;")

        return ' '.join(styles)

    def generate_text_block(self, length_type='medium', add_paragraphs=None):
        """
        Генерирует текстовый блок из загруженных файлов
        length_type: 'short', 'medium', 'long', 'very_long'
        add_paragraphs: None (случайно), True, False
        """
        # Получаем текст
        text = self.get_text_by_length(length_type)

        if text is None:
            return "<p>Текст не найден</p>"

        # Обрезаем текст в зависимости от желаемой длины
        words = text.split()
        total_words = len(words)

        if length_type == 'short':
            target_words = random.randint(10, 30)
        elif length_type == 'medium':
            target_words = random.randint(50, 150)
        elif length_type == 'long':
            target_words = random.randint(200, 500)
        else:  # very_long
            target_words = random.randint(600, 1500)

        # Если текст слишком короткий, берем его целиком
        if total_words <= target_words:
            final_text = text
        else:
            # Берем случайный кусок текста
            start = random.randint(0, max(0, total_words - target_words))
            final_text = ' '.join(words[start:start + target_words])

        # Решаем, добавлять ли параграфы
        if add_paragraphs is None:
            add_paragraphs = random.random() < 0.6

        # Разбиваем на параграфы
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

        # Случайный шрифт для блока
        font_family = self.generate_random_font_style()

        # Форматируем текст с параграфами
        formatted_paragraphs = []
        for i, paragraph in enumerate(paragraphs):
            # Генерируем случайный стиль для каждого параграфа
            style = self.generate_random_text_style()

            # Для первого параграфа убираем верхний отступ
            if i == 0:
                style = re.sub(r'margin-top: \d+px;', 'margin-top: 0;', style)

            formatted_paragraphs.append(f"<p style='{style}'>{paragraph}</p>")

        # Стиль для заголовка
        title_style = f"font-family: {font_family}; font-size: {random.randint(14, 18)}px;"
        title_style += f" font-weight: {random.choice(['bold', 'normal'])};"
        if random.random() > 0.7:
            title_style += f" color: {random.choice(['#2c3e50', '#2980b9', '#1a5276'])};"
        if random.random() > 0.8:
            title_style += " text-decoration: underline;"

        # Собираем весь блок с общим шрифтом
        block_style = f"font-family: {font_family};"

        formatted_text = f"<div style='{block_style}'>"
        formatted_text += f"<h3 style='{title_style}; margin-bottom: 8px;'>{title}</h3>\n"
        formatted_text += '\n'.join(formatted_paragraphs)
        formatted_text += "</div>"

        return formatted_text


class TextBlockPDFGenerator:
    """Генератор PDF с текстовыми блоками из локальных файлов"""

    def __init__(self, text_dir="texts", output_dir="generated_pdfs_text"):
        self.text_dir = Path(text_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp_html_text")
        self.temp_dir.mkdir(exist_ok=True)
        self.text_generator = LocalTextGenerator(text_dir)

    def create_html_page_with_texts(self, text_blocks, blocks_per_page=1):
        """Создает HTML-страницу с текстовыми блоками"""
        if not text_blocks:
            return '<div>Нет текста</div>'

        formatted_blocks = [str(block) for block in text_blocks if block]

        # Случайные отступы между блоками
        block_gap = random.choice(['10', '15', '20', '25', '30'])

        if blocks_per_page == 1:
            width_percent = random.choice(['85', '90', '92', '95'])
            padding = random.choice(['10', '15', '20'])

            content = f'''
            <div style="width: 100%; height: 100%; display: flex; align-items: flex-start; justify-content: center; overflow: hidden;">
                <div style="width: {width_percent}%; max-height: 95%; overflow: hidden; padding: {padding}px; text-align: justify;">
                    {formatted_blocks[0] if formatted_blocks else ''}
                </div>
            </div>
            '''
        elif blocks_per_page == 2:
            gap = random.choice(['15', '20', '25'])
            padding = random.choice(['5', '8', '10'])

            content = f'''
            <div style="display: flex; gap: {gap}px; height: 100%; width: 100%; align-items: flex-start; padding: {padding}px;">
                <div style="flex: 1; min-width: 0; height: 100%; overflow: hidden; padding: 5px;">
                    {formatted_blocks[0] if len(formatted_blocks) > 0 else ''}
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; overflow: hidden; padding: 5px;">
                    {formatted_blocks[1] if len(formatted_blocks) > 1 else ''}
                </div>
            </div>
            '''
        else:  # 3 колонки
            gap = random.choice(['10', '12', '15'])
            padding = random.choice(['3', '5', '8'])

            content = f'''
            <div style="display: flex; gap: {gap}px; height: 100%; width: 100%; align-items: flex-start; padding: {padding}px;">
                <div style="flex: 1; min-width: 0; height: 100%; overflow: hidden; padding: 3px;">
                    {formatted_blocks[0] if len(formatted_blocks) > 0 else ''}
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; overflow: hidden; padding: 3px;">
                    {formatted_blocks[1] if len(formatted_blocks) > 1 else ''}
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; overflow: hidden; padding: 3px;">
                    {formatted_blocks[2] if len(formatted_blocks) > 2 else ''}
                </div>
            </div>
            '''

        # Случайно добавляем рамку или фон
        page_style = ""
        if random.random() > 0.9:
            page_style = "border: 1px solid #e0e0e0; border-radius: 8px;"
        if random.random() > 0.95:
            page_style += " background-color: #fafafa;"

        return f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ margin: 0; padding: 0; background: white; height: 100vh; width: 100vw; display: flex; align-items: center; justify-content: center; }}
    .page-container {{ width: 100%; height: 100%; max-width: 1200px; max-height: 800px; padding: {random.choice(['15', '20', '25'])}px; display: flex; align-items: flex-start; justify-content: center; {page_style} }}
    h3 {{ margin: 0 0 8px 0; }}
    p {{ margin: 0; }}
    @media print {{ body {{ margin: 0; padding: 0; }} .page-container {{ max-width: 100%; max-height: 100%; padding: 10px; }} }}
</style>
</head>
<body><div class="page-container">{content}</div></body>
</html>'''

    def generate_pdf_with_playwright(self, html_pages, pdf_path):
        """Генерирует PDF через Playwright с использованием классов"""
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

    def generate_group(self, group_name, text_length, num_pdfs=30, pages_per_pdf=100):
        """Генерирует группу PDF файлов с случайным количеством колонок (1, 2 или 3)"""
        length_label = "короткий" if text_length == 'short' else "длинный"
        print(f"\n📁 Группа '{group_name}' ({length_label} текст, случайное кол-во колонок 1-3)")
        print(f"  PDF: {num_pdfs}, страниц: {pages_per_pdf}")

        group_dir = self.output_dir / group_name
        group_dir.mkdir(exist_ok=True)

        # Статистика по колонкам
        columns_stats = {1: 0, 2: 0, 3: 0}

        for pdf_num in range(1, num_pdfs + 1):
            print(f"  📄 PDF {pdf_num}/{num_pdfs}...")
            all_pages = []

            for page_num in range(pages_per_pdf):
                # Случайно выбираем количество колонок (1, 2 или 3)
                blocks_per_page = random.choice([1, 2, 3])
                columns_stats[blocks_per_page] += 1

                # Генерируем текстовые блоки для страницы
                text_blocks = []
                for _ in range(blocks_per_page):
                    block = self.text_generator.generate_text_block(text_length)
                    text_blocks.append(block)

                # Создаем HTML страницы с текстами
                page_html = self.create_html_page_with_texts(text_blocks, blocks_per_page)
                all_pages.append(page_html)

            # Сохраняем PDF
            pdf_path = group_dir / f"text_{pdf_num:03d}.pdf"
            success = self.generate_pdf_with_playwright(all_pages, pdf_path)

            if success:
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"    ✅ Создан ({size_mb:.2f} MB)")
            else:
                print(f"    ❌ Ошибка при создании PDF {pdf_num}")

        # Выводим статистику по колонкам
        total_pages = num_pdfs * pages_per_pdf
        print(f"\n  📊 Статистика использования колонок:")
        for cols, count in columns_stats.items():
            percentage = (count / total_pages) * 100
            print(f"    {cols} колонки: {count} страниц ({percentage:.1f}%)")

    def generate_all_groups(self):
        """Генерирует две группы: с коротким и длинным текстом"""
        groups = [
            ('group_short_text', 'short'),
            ('group_long_text', 'very_long'),
        ]

        for group_name, text_length in groups:
            self.generate_group(group_name, text_length)

        print("\n" + "=" * 50)
        print("✅ ВСЕ ГРУППЫ PDF С ТЕКСТОМ СГЕНЕРИРОВАНЫ!")
        print("=" * 50)


def main():
    # Параметры
    text_directory = "bbc-fulltext (document classification)/bbc/"
    output_directory = "generated_pdfs_text"

    # Проверяем наличие текстовых файлов
    if not Path(text_directory).exists():
        print(f"❌ Директория '{text_directory}' не найдена!")
        print(f"Создайте папку '{text_directory}' и поместите в нее .txt файлы.")
        print(f"Поддерживаются файлы в поддиректориях.")
        return

    # Проверяем наличие txt файлов
    txt_files = list(Path(text_directory).rglob("*.txt"))
    if not txt_files:
        print(f"❌ В директории '{text_directory}' нет .txt файлов!")
        print(f"Поместите .txt файлы в папку '{text_directory}' или ее поддиректории.")
        return

    # Очищаем временные файлы
    temp_dir = Path("temp_html_text")
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    # Создаем генератор и запускаем
    generator = TextBlockPDFGenerator(text_directory, output_directory)

    # Проверяем, что есть тексты
    total_texts = sum(len(texts) for texts in generator.text_generator.texts_by_length.values())
    if total_texts == 0:
        print("❌ Не удалось загрузить тексты! Проверьте содержимое файлов.")
        return

    generator.generate_all_groups()

    # Выводим статистику
    total_pdfs = 2 * 30
    total_pages = total_pdfs * 100

    print("\n📊 СТАТИСТИКА:")
    print(f"  📁 Всего PDF файлов: {total_pdfs}")
    print(f"  📄 Всего страниц: {total_pages}")
    print(f"  📝 Всего текстовых блоков: ~{total_pages * 2:,}")
    print(f"  📁 Выходная директория: {output_directory}")

    # Проверяем размер
    output_dir = Path(output_directory)
    if output_dir.exists():
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*.pdf")) / (1024 * 1024)
        print(f"  💾 Общий размер: {total_size:.2f} MB")

    print("\n📁 Структура выходных файлов:")
    print(f"  {output_directory}/")
    print("  ├── group_short_text/      # Короткий текст (1-3 колонки случайно)")
    print("  │   └── text_001.pdf ...")
    print("  └── group_long_text/       # Длинный текст (1-3 колонки случайно)")
    print("      └── text_001.pdf ...")


if __name__ == "__main__":
    main()
