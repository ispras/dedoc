import argparse
import importlib.util
import logging
import os
import sys

parser_config = argparse.ArgumentParser()
parser_config.add_argument("-c", "--config_path", help="path to configuration file")
parser_config.add_argument("-m", "--module", help="Only for tests")
parser_config.add_argument("-f", "--test_files", metavar="VALUE", nargs='*', help="Only for tests")
parser_config.add_argument('-v', "--unitest_verbose_mode", nargs='?', help="to enable verbose mode of unittest. Only for tests")
args_config = parser_config.parse_args()

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")


_config = dict(
    # --------------------------------------------JOBLIB SETTINGS-------------------------------------------------------
    # number of parallel jobs in some tasks as OCR
    n_jobs=1,

    # ---------------------------------------------API SETTINGS---------------------------------------------------------
    # max file size in bytes
    max_content_length=512 * 1024 * 1024,
    # application port
    api_port=int(os.environ.get('DOCREADER_PORT', '1231')),
    static_files_dirs={},
    # log settings
    logger=logging.getLogger(),
    import_path_init_api_args="src.api.api_args",

    # -------------------------------------------ATTACHMENT ANALYSE-----------------------------------------------------
    # analyse content of attachments
    need_content_analysis=True,
    recursion_deep_attachments=10,

    # -------------------------------------------RECOGNIZE SETTINGS-----------------------------------------------------
    # TESSERACT OCR confidence threshold ( values: [-1 - undefined;  0.0 : 100.0 % - confidence value)
    ocr_conf_threshold=40.0,
    # max depth of document structure tree
    recursion_deep_subparagraphs=30
)


class Configuration(object):
    """
    Pattern Singleton for configuration service
    INFO: Configuration class and config are created once at the first call
    """
    __instance = None
    __config = None

    @classmethod
    def getInstance(cls: "Configuration") -> "Configuration":
        """
        Actual object creation will happen when we use Configuration.getInstance()
        """
        if not cls.__instance:
            cls.__instance = Configuration()

        return cls.__instance

    def __initConfig(self) -> None:
        if args_config.config_path is not None:
            spec = importlib.util.spec_from_file_location("config_module", args_config.config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            self.__config = config_module._config
        else:
            self.__config = _config

    def getConfig(self) -> dict:
        if self.__config is None:
            self.__initConfig()
        return self.__config


def get_config() -> dict:
    return Configuration().getConfig()
