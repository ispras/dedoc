import argparse
import os
from pathlib import Path
import random

from pypdf import PdfReader, PdfWriter

PAGES_NUMBERS = [1, 5, 10, 25, 50, 100]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', type=Path)
    parser.add_argument('out_dir', type=Path)
    args = parser.parse_args()

    for file_path in args.in_dir.rglob('*.pdf'):
        parent_dir = file_path.parent.name
        out_parent_dir = args.out_dir / parent_dir
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)

        for n in PAGES_NUMBERS:
            n_dir = out_parent_dir / str(n)
            os.makedirs(n_dir, exist_ok=True)
            random_pages = sorted(random.sample(range(total_pages), n))
            writer = PdfWriter()
            for page_num in random_pages:
                writer.add_page(reader.pages[page_num])
            output_path = n_dir / file_path.name

            with output_path.open('wb') as out_f:
                writer.write(out_f)
