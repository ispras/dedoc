import base64
import random
import time
from pathlib import Path

from playwright.sync_api import PdfMargins, ViewportSize
from playwright.sync_api import sync_playwright


class ImagePDFGenerator:
    """Генератор PDF с изображениями из папки"""

    def __init__(self, images_dir="images", output_dir="generated_pdfs_images"):
        self.images_dir = Path(images_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("temp_html_images")
        self.temp_dir.mkdir(exist_ok=True)

        # Загружаем изображения из папки
        self.image_files = self.load_images()
        print(f"Загружено {len(self.image_files)} изображений из {self.images_dir}")

    def load_images(self):
        """Загружает все изображения из папки"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
        images = []

        if not self.images_dir.exists():
            print(f"⚠️ Директория {self.images_dir} не найдена!")
            return []

        # Рекурсивно ищем все изображения
        for ext in image_extensions:
            images.extend(self.images_dir.rglob(f"*{ext}"))
            images.extend(self.images_dir.rglob(f"*{ext.upper()}"))

        # Сортируем для воспроизводимости
        images = sorted(images)

        if not images:
            print(f"⚠️ В директории {self.images_dir} не найдено изображений!")
            print(f"Поддерживаемые форматы: {', '.join(image_extensions)}")

        return images

    def get_random_images(self, count):
        """Возвращает случайные изображения из загруженных"""
        if not self.image_files:
            print("❌ Нет доступных изображений!")
            return []

        if len(self.image_files) < count:
            # Если изображений меньше, чем нужно, используем с повторением
            print(f"⚠️ Доступно только {len(self.image_files)} изображений, требуется {count}")
            return random.choices(self.image_files, k=count)

        return random.sample(self.image_files, count)

    def image_to_base64(self, image_path):
        """Конвертирует изображение в base64 для вставки в HTML"""
        try:
            with open(image_path, 'rb') as f:
                img_data = f.read()

            # Определяем MIME тип
            suffix = image_path.suffix.lower()
            if suffix == '.png':
                mime_type = 'image/png'
            elif suffix in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif suffix == '.bmp':
                mime_type = 'image/bmp'
            elif suffix == '.tiff':
                mime_type = 'image/tiff'
            elif suffix == '.gif':
                mime_type = 'image/gif'
            else:
                mime_type = 'image/png'

            base64_data = base64.b64encode(img_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_data}"
        except Exception as e:
            print(f"  Ошибка при конвертации {image_path.name}: {e}")
            return None

    def create_html_page_with_images(self, image_paths, images_per_page=1):
        """Создает HTML-страницу с изображениями"""
        # Конвертируем изображения в base64
        images_base64 = []
        for img_path in image_paths:
            if img_path and img_path.exists():
                img_base64 = self.image_to_base64(img_path)
                if img_base64:
                    images_base64.append(img_base64)

        if not images_base64:
            return '<div>Нет изображений</div>'

        # Создаем HTML для размещения изображений
        if images_per_page == 1:
            images_html_content = f'''
            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
                <img src="{images_base64[0]}" style="max-width: 95%; max-height: 95%; object-fit: contain;" />
            </div>
            '''
        elif images_per_page == 2:
            images_html_content = f'''
            <div style="display: flex; gap: 15px; height: 100%; width: 100%; align-items: center; justify-content: center;">
                <div style="flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{images_base64[0] if len(images_base64) > 0 else ''}" style="max-width: 100%; max-height: 95%; object-fit: contain;" />
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{images_base64[1] if len(images_base64) > 1 else ''}" style="max-width: 100%; max-height: 95%; object-fit: contain;" />
                </div>
            </div>
            '''
        else:  # 3 изображения
            images_html_content = f'''
            <div style="display: flex; gap: 10px; height: 100%; width: 100%; align-items: center; justify-content: center;">
                <div style="flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{images_base64[0] if len(images_base64) > 0 else ''}" style="max-width: 100%; max-height: 95%; object-fit: contain;" />
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{images_base64[1] if len(images_base64) > 1 else ''}" style="max-width: 100%; max-height: 95%; object-fit: contain;" />
                </div>
                <div style="flex: 1; min-width: 0; height: 100%; display: flex; align-items: center; justify-content: center;">
                    <img src="{images_base64[2] if len(images_base64) > 2 else ''}" style="max-width: 100%; max-height: 95%; object-fit: contain;" />
                </div>
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
            padding: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        img {{
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}
            .page-container {{
                max-width: 100%;
                max-height: 100%;
                padding: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        {images_html_content}
    </div>
</body>
</html>'''

    def generate_pdf_with_playwright(self, html_pages, pdf_path):
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
            padding: 8mm;
            margin: 0 auto;
            page-break-after: always;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            background: white;
        }
        .page-content {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        img {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        @media print {
            .page { 
                page-break-after: always;
                margin: 0;
                padding: 5mm;
                width: 210mm;
                height: 297mm;
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

    def generate_group(self, group_name, images_per_page, num_pdfs=30, pages_per_pdf=100):
        """Генерирует группу PDF файлов"""
        print(f"\n📁 Генерация группы '{group_name}' ({images_per_page} изображений на странице)")
        print(f"  PDF файлов: {num_pdfs}, страниц в PDF: {pages_per_pdf}")
        print(f"  Всего изображений нужно: {num_pdfs * pages_per_pdf * images_per_page}")

        if not self.image_files:
            print("❌ Нет изображений для генерации!")
            return

        group_dir = self.output_dir / group_name
        group_dir.mkdir(exist_ok=True)

        for pdf_num in range(1, num_pdfs + 1):
            print(f"  📄 Генерация PDF {pdf_num}/{num_pdfs}...")

            all_pages = []

            for page_num in range(pages_per_pdf):
                # Выбираем случайные изображения для страницы
                images_for_page = self.get_random_images(images_per_page)

                # Создаем HTML страницы с изображениями
                page_html = self.create_html_page_with_images(images_for_page, images_per_page)
                all_pages.append(page_html)

            # Сохраняем PDF
            pdf_path = group_dir / f"images_{pdf_num:03d}.pdf"
            success = self.generate_pdf_with_playwright(all_pages, pdf_path)

            if success:
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                print(f"    ✅ PDF {pdf_num} создан ({size_mb:.2f} MB)")
            else:
                print(f"    ❌ Ошибка при создании PDF {pdf_num}")

    def generate_all_groups(self):
        """Генерирует все три группы PDF с изображениями"""
        groups = [
            ('group_1_image', 1),  # 1 изображение на странице
            ('group_2_images', 2),  # 2 изображения на странице
            ('group_3_images', 3),  # 3 изображения на странице
        ]

        for group_name, images_per_page in groups:
            self.generate_group(group_name, images_per_page)

        print("\n" + "=" * 50)
        print("✅ ВСЕ ГРУППЫ PDF С ИЗОБРАЖЕНИЯМИ СГЕНЕРИРОВАНЫ!")
        print("=" * 50)


def main():
    # Параметры
    images_directory = "archive/PetImages/Cat/"  # Папка с вашими изображениями
    output_directory = "generated_pdfs_images"

    # Проверяем наличие изображений
    if not Path(images_directory).exists():
        print(f"⚠️ Директория '{images_directory}' не найдена!")
        print(f"Создайте папку '{images_directory}' и поместите в нее изображения.")
        print(f"Или укажите правильный путь к папке с изображениями.")
        return

    # Создаем генератор и запускаем
    generator = ImagePDFGenerator(images_directory, output_directory)

    if not generator.image_files:
        print(f"❌ В папке '{images_directory}' нет изображений!")
        print(f"Поддерживаемые форматы: PNG, JPG, JPEG, BMP, TIFF, GIF")
        return

    generator.generate_all_groups()

    # Выводим статистику
    total_pdfs = 30 * 3  # 3 группы по 30 PDF
    total_pages = total_pdfs * 100  # В каждом PDF 100 страниц
    total_images = total_pages * 2  # В среднем 2 изображения на странице (1+2+3)/3

    print("\n📊 СТАТИСТИКА:")
    print(f"  📁 Всего PDF файлов: {total_pdfs}")
    print(f"  📄 Всего страниц: {total_pages}")
    print(f"  🖼️ Всего изображений использовано: ~{total_images:,}")
    print(f"  📂 Папка с изображениями: {images_directory}")
    print(f"  📁 Выходная директория: {output_directory}")

    # Проверяем размер
    output_dir = Path(output_directory)
    if output_dir.exists():
        total_size = sum(f.stat().st_size for f in output_dir.rglob("*.pdf")) / (1024 * 1024)
        print(f"  💾 Общий размер: {total_size:.2f} MB")


if __name__ == "__main__":
    main()
