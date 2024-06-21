from dedoc.docs.sourse._static.code_examples.langchain.base_dedoc_file_loader import BaseDedocFileLoader


class DedocPDFLoader(BaseDedocFileLoader):
    """
    This loader provides part of the functionality of DedocFileLoader and allows you to load PDF files.
    To do this, the Dedoc library contains methods for working with documents with and without a text layer.
    More information is available at the link:
    https://dedoc.readthedocs.io/en/latest/?badge=latest
    """
    def make_config(  # noqa FOL005
        self
    ) -> dict:
        from dedoc.utils.langchain import make_manager_pdf_config
        return make_manager_pdf_config(file_path=self.file_path, parsing_params=self.parsing_params, split=self.split)
