from dedoc.docs.sourse._static.code_examples.langchain.base_dedoc_file_loader import BaseDedocFileLoader


class DedocFileLoader(BaseDedocFileLoader):
    """
    This loader allows you to use almost all the functionality of the Dedoc library.
    Dedoc supports documents of different formats, including .pdf, .png, .docx, .txt, and many more.
    More information is available at the link:
    https://dedoc.readthedocs.io/en/latest/?badge=latest
    """
    def make_config(  # noqa FOL005
        self
    ) -> dict:
        from dedoc.utils.langchain import make_manager_config
        return make_manager_config(file_path=self.file_path, parsing_params=self.parsing_params, split=self.split)
