import logging
import time

from bs4 import Tag


class Counter:

    def __init__(self, body: Tag, logger: logging.Logger) -> None:
        self.logger = logger
        self.total_paragraph_number = sum([len(p.find_all('w:p')) for p in body if p.name != 'p' and p.name != "tbl" and isinstance(p, Tag)])
        self.total_paragraph_number += len([p for p in body if p.name == 'p' and isinstance(p, Tag)])
        self.current_paragraph_number = 0
        self.checkpoint_time = time.time()

    def inc(self) -> None:
        self.current_paragraph_number += 1
        current_time = time.time()
        if current_time - self.checkpoint_time > 3:
            self.logger.info(f"Processed {self.current_paragraph_number} paragraphs from {self.total_paragraph_number}")
            self.checkpoint_time = current_time
