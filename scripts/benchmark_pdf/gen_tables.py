import random
import time
from pathlib import Path

from playwright.sync_api import PdfMargins, ViewportSize, sync_playwright


class AdvancedTableGenerator:
    """Генератор HTML-таблиц с объединенными ячейками"""

    def __init__(self):
        self.texts_ru = [
            'Данные', 'Значение', 'Показатель', 'Результат', 'Процесс',
            'Система', 'Функция', 'Параметр', 'Алгоритм', 'Метод',
            'Анализ', 'Отчет', 'Статистика', 'Выборка', 'Интервал',
            'Коэффициент', 'Индекс', 'Погрешность', 'Отклонение', 'Среднее',
            'Максимум', 'Минимум', 'Сумма', 'Процент', 'Доля',
            'Итого', 'Всего', 'Среднее', 'Медиана', 'Мода'
        ]

    def get_random_text(self, words=2):
        return ' '.join(random.choices(self.texts_ru, k=words))

    def get_random_value(self):
        """Генерирует случайное значение для ячейки"""
        cell_type = random.choice(['text', 'number', 'date', 'mixed'])
        if cell_type == 'text':
            return self.get_random_text(random.randint(1, 4))
        elif cell_type == 'number':
            num = random.randint(1, 9999)
            if random.random() > 0.7:
                return f"{num:,.0f}".replace(',', ' ')
            return str(num)
        elif cell_type == 'date':
            return f"{random.randint(1, 28):02d}.{random.randint(1, 12):02d}.{random.randint(2020, 2025)}"
        else:
            return random.choice([
                self.get_random_text(2),
                str(random.randint(1, 999)),
                f"{random.randint(1, 28):02d}.{random.randint(1, 12):02d}.{random.randint(2020, 2025)}"
            ])

    def generate_table_structure(self, min_rows=5, max_rows=12, min_cols=3, max_cols=7):
        """Генерирует структуру таблицы с объединенными ячейками без пересечений"""
        rows = random.randint(min_rows, max_rows)
        cols = random.randint(min_cols, max_cols)

        # Инициализируем сетку
        grid = [[None for _ in range(cols)] for _ in range(rows)]

        # Сначала заполняем все ячейки данными
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] is None:
                    grid[r][c] = {
                        'data': self.get_random_value(),
                        'rowspan': 1,
                        'colspan': 1,
                        'is_header': False,
                        'bg_color': None
                    }

        # Теперь добавляем объединения
        merge_attempts = 0
        max_merges = min(rows * cols // 6, 8)

        while merge_attempts < 30 and max_merges > 0:
            # Выбираем случайную ячейку для объединения
            r = random.randint(0, rows - 2)
            c = random.randint(0, cols - 2)

            # Проверяем, что ячейка существует и не объединена
            if grid[r][c] is None:
                merge_attempts += 1
                continue

            # Проверяем, что это не объединенная ячейка
            if isinstance(grid[r][c], dict):
                if grid[r][c].get('rowspan', 1) > 1 or grid[r][c].get('colspan', 1) > 1:
                    merge_attempts += 1
                    continue
            else:
                merge_attempts += 1
                continue

            # Определяем размер объединения
            max_rowspan = min(3, rows - r)
            max_colspan = min(3, cols - c)

            # Проверяем, что все ячейки для объединения свободны
            free = True
            for i in range(r, r + max_rowspan):
                for j in range(c, c + max_colspan):
                    if i >= rows or j >= cols:
                        free = False
                        break
                    if grid[i][j] is None:
                        free = False
                        break
                    if isinstance(grid[i][j], dict):
                        if grid[i][j].get('rowspan', 1) > 1 or grid[i][j].get('colspan', 1) > 1:
                            free = False
                            break
                    else:
                        free = False
                        break
                if not free:
                    break

            if free and max_rowspan > 1 and max_colspan > 1:
                # Делаем объединение
                data = self.get_random_value()
                is_header = random.random() < 0.2 and r == 0

                grid[r][c] = {
                    'data': data,
                    'rowspan': max_rowspan,
                    'colspan': max_colspan,
                    'is_header': is_header,
                    'bg_color': '#e8f4f8' if is_header else '#f9f9f9'
                }

                # Помечаем остальные ячейки как объединенные
                for i in range(r, r + max_rowspan):
                    for j in range(c, c + max_colspan):
                        if i != r or j != c:
                            grid[i][j] = None  # Помечаем как объединенные

                max_merges -= 1

            merge_attempts += 1

        # Добавляем заголовки в первую строку
        if random.random() < 0.7:
            for c in range(cols):
                if grid[0][c] is not None and isinstance(grid[0][c], dict):
                    if grid[0][c].get('rowspan', 1) == 1 and grid[0][c].get('colspan', 1) == 1:
                        grid[0][c]['is_header'] = True
                        grid[0][c]['bg_color'] = '#f0f0f0'

        return grid

    def generate_html_table(self, grid):
        """Генерирует HTML-код таблицы с объединенными ячейками"""
        if not grid:
            return '<table></table>'

        rows = len(grid)
        html = [
            '<table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 9px; table-layout: fixed;">']

        # Генерируем тело таблицы
        html.append('<tbody>')
        for r in range(rows):
            html.append('<tr>')
            for c in range(len(grid[r])):
                cell = grid[r][c]
                # Пропускаем объединенные ячейки (None)
                if cell is None:
                    continue

                # Проверяем, что это словарь
                if not isinstance(cell, dict):
                    continue

                rowspan = cell.get('rowspan', 1)
                colspan = cell.get('colspan', 1)
                data = cell.get('data', '')
                is_header = cell.get('is_header', False)
                bg_color = cell.get('bg_color', '')

                # Стили ячейки
                style = 'border: 1px solid #333; padding: 4px 6px; text-align: center; word-wrap: break-word;'
                if bg_color:
                    style += f' background-color: {bg_color};'
                if is_header:
                    style += ' font-weight: bold;'

                # Случайное форматирование
                if random.random() > 0.95:
                    style += ' color: #c0392b;'
                if random.random() > 0.97:
                    style += ' font-style: italic;'

                # Создаем тег
                tag = 'th' if is_header else 'td'
                attrs = []
                if rowspan > 1:
                    attrs.append(f'rowspan="{rowspan}"')
                if colspan > 1:
                    attrs.append(f'colspan="{colspan}"')

                attrs_str = ' ' + ' '.join(attrs) if attrs else ''
                html.append(f'<{tag}{attrs_str} style="{style}">{data}</{tag}>')
            html.append('</tr>')
        html.append('</tbody>')
        html.append('</table>')

        return '\n'.join(html)

    def create_html_page(self, tables_html, tables_per_page=1):
        """Создает HTML-страницу с одной или несколькими таблицами"""
        if tables_per_page == 1:
            tables_html_content = tables_html[0] if tables_html else ''
        elif tables_per_page == 2:
            tables_html_content = f'''
            <div style="display: flex; gap: 15px; height: 100%; width: 100%;">
                <div style="flex: 1; min-width: 0; display: flex; align-items: center;">{tables_html[0] if len(tables_html) > 0 else ''}</div>
                <div style="flex: 1; min-width: 0; display: flex; align-items: center;">{tables_html[1] if len(tables_html) > 1 else ''}</div>
            </div>
            '''
        else:  # 3 таблицы
            tables_html_content = f'''
            <div style="display: flex; gap: 10px; height: 100%; width: 100%;">
                <div style="flex: 1; min-width: 0; display: flex; align-items: center;">{tables_html[0] if len(tables_html) > 0 else ''}</div>
                <div style="flex: 1; min-width: 0; display: flex; align-items: center;">{tables_html[1] if len(tables_html) > 1 else ''}</div>
                <div style="flex: 1; min-width: 0; display: flex; align-items: center;">{tables_html[2] if len(tables_html) > 2 else ''}</div>
            </div>
            '''

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            background: white;
            font-family: Arial, sans-serif;
            height: 100vh;
            width: 100vw;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .page-container {{
            width: 100%;
            height: 100%;
            max-width: 1200px;
            max-height: 800px;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0;
        }}
        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}
            .page-container {{
                max-width: 100%;
                max-height: 100%;
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        {tables_html_content}
    </div>
</body>
</html>'''


class TablePDFGenerator:
    """Основной класс для генерации PDF с таблицами"""

    def __init__(self, output_dir="generated_pdfs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.generator = AdvancedTableGenerator()
        self.temp_dir = Path("temp_html")
        self.temp_dir.mkdir(exist_ok=True)

    def generate_pdf_with_playwright(self, html_pages, pdf_path, tables_per_page=1):
        """Генерирует PDF из HTML-страниц с помощью Playwright"""
        try:
            # Создаем один HTML файл со всеми страницами
            full_html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            margin: 0; 
            padding: 0; 
            background: white;
            font-family: Arial, sans-serif;
        }
        .page { 
            width: 210mm;
            height: 297mm;
            padding: 10mm;
            margin: 0 auto;
            page-break-after: always;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
        }
        .page-content {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 9px;
        }
        td, th {
            border: 1px solid #333;
            padding: 4px 6px;
            text-align: center;
            word-wrap: break-word;
        }
        .tables-container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .tables-row {
            display: flex;
            gap: 10px;
            flex: 1;
            min-height: 0;
        }
        .table-wrapper {
            flex: 1;
            min-width: 0;
            display: flex;
            align-items: center;
        }
        .table-wrapper table {
            width: 100%;
        }
        @media print {
            .page { 
                page-break-after: always;
                margin: 0;
                padding: 8mm;
            }
        }
    </style>
</head>
<body>'''

            # Добавляем каждую страницу
            for page_html in html_pages:
                # Извлекаем содержимое body
                start = page_html.find('<body>') + 6
                end = page_html.find('</body>')
                body_content = page_html[start:end] if start != -1 and end != -1 else page_html

                full_html += f'''
                <div class="page">
                    <div class="page-content">
                        {body_content}
                    </div>
                </div>'''

            full_html += '</body></html>'

            # Сохраняем во временный файл
            temp_html = self.temp_dir / f"temp_{hash(pdf_path)}.html"
            with open(temp_html, 'w', encoding='utf-8') as f:
                f.write(full_html)

            # Генерируем PDF
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )

                page = browser.new_page(viewport=ViewportSize(width=1920, height=1080))
                page.goto(f'file://{temp_html.absolute()}')
                page.wait_for_load_state('networkidle')

                # Добавляем небольшую задержку для рендеринга
                time.sleep(0.3)

                # Генерируем PDF
                page.pdf(
                    path=str(pdf_path),
                    format='A4',
                    print_background=True,
                    margin=PdfMargins(top="20px", right="20px", bottom="20px", left="20px")
                )

                browser.close()

            # Удаляем временный файл
            if temp_html.exists():
                temp_html.unlink()

            return True

        except Exception as e:
            print(f"  Ошибка при генерации PDF: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_group(self, group_name, tables_per_page, num_pdfs=30, pages_per_pdf=100):
        """Генерирует группу PDF файлов"""
        print(f"\n📁 Генерация группы '{group_name}' ({tables_per_page} таблиц на странице)")
        print(f"  PDF файлов: {num_pdfs}, страниц в PDF: {pages_per_pdf}")

        group_dir = self.output_dir / group_name
        group_dir.mkdir(exist_ok=True)

        for pdf_num in range(1, num_pdfs + 1):
            print(f"  📄 Генерация PDF {pdf_num}/{num_pdfs}...")

            all_pages = []

            for page_num in range(pages_per_pdf):
                # Генерируем таблицы для страницы
                page_tables = []
                for _ in range(tables_per_page):
                    grid = self.generator.generate_table_structure()
                    table_html = self.generator.generate_html_table(grid)
                    page_tables.append(table_html)

                # Создаем HTML страницы с таблицами
                page_html = self.generator.create_html_page(page_tables, tables_per_page)
                all_pages.append(page_html)

            # Сохраняем PDF
            pdf_path = group_dir / f"tables_{pdf_num:03d}.pdf"
            success = self.generate_pdf_with_playwright(all_pages, pdf_path, tables_per_page)

            if success:
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"    ✅ PDF {pdf_num} создан ({size_mb:.2f} MB)")
            else:
                print(f"    ❌ Ошибка при создании PDF {pdf_num}")

    def generate_all_groups(self):
        """Генерирует все три группы PDF"""
        groups = [
            ('group_1_table', 1),
            ('group_2_tables', 2),
            ('group_3_tables', 3),
        ]

        for group_name, tables_per_page in groups:
            self.generate_group(group_name, tables_per_page)

        print("\n" + "=" * 50)
        print("✅ ВСЕ ГРУППЫ PDF СГЕНЕРИРОВАНЫ!")
        print("=" * 50)


def main():
    # Очищаем старые временные файлы
    temp_dir = Path("temp_html")
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    # Создаем генератор и запускаем
    generator = TablePDFGenerator("generated_pdfs")
    generator.generate_all_groups()

    # Выводим статистику
    total_pdfs = 30 * 3
    total_pages = total_pdfs * 100
    total_tables = total_pages * 2

    print("\n📊 СТАТИСТИКА:")
    print(f"  📁 Всего PDF файлов: {total_pdfs}")
    print(f"  📄 Всего страниц: {total_pages}")
    print(f"  📊 Всего таблиц: ~{total_tables:,}")

    # Проверяем размер
    output_dir = Path("generated_tables")
    if output_dir.exists():
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*.pdf")) / (1024 * 1024)
        print(f"  💾 Общий размер: {total_size:.2f} MB")


if __name__ == "__main__":
    main()
