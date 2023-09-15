import os
from typing import Optional

from dedoc.converters.concrete_converters.abstract_converter import AbstractConverter


class DjvuConverter(AbstractConverter):

    def __init__(self, config):
        super().__init__(config=config)

    def can_convert(self,
                    extension: str,
                    mime: str,
                    parameters: Optional[dict] = None) -> bool:
        return extension == '.djvu'

    def do_convert(self,
                   tmp_dir: str,
                   filename: str,
                   extension: str) -> str:
        os.system("ddjvu -format=pdf "
                  "{tmp_dir}/{filename}{extension} {tmp_dir}/{filename}.pdf".format(tmp_dir=tmp_dir,
                                                                                    filename=filename,
                                                                                    extension=extension))
        self._await_for_conversion(filename + '.pdf', tmp_dir)
        return filename + '.pdf'