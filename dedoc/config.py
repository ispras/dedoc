import logging
import os
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")

DEBUG_MODE = False
RESOURCES_PATH = os.environ.get("RESOURCES_PATH", os.path.join(os.path.expanduser("~"), ".cache", "dedoc", "resources"))

_config = dict(
    # -----------------------------------------RESOURCES PATH SETTINGS----------------------------------------------------
    resources_path=RESOURCES_PATH,
    intermediate_data_path=os.path.join(RESOURCES_PATH, "datasets"),
    table_path="/tmp/tables",

    # -----------------------------------------COMMON DEBUG SETTINGS----------------------------------------------------
    debug_mode=DEBUG_MODE,
    path_debug=os.path.join(os.path.abspath(os.sep), "tmp", "dedoc"),

    # --------------------------------------------JOBLIB SETTINGS-------------------------------------------------------
    # number of parallel jobs in some tasks as OCR
    n_jobs=1,

    # --------------------------------------------GPU SETTINGS----------------------------------------------------------
    # set gpu in XGBoost and torch models
    on_gpu=False,

    # ---------------------------------------------API SETTINGS---------------------------------------------------------
    # max file size in bytes
    max_content_length=512 * 1024 * 1024,
    # application port
    api_port=int(os.environ.get("DOCREADER_PORT", "1231")),
    static_files_dirs={},
    # log settings
    logger=logging.getLogger(),
    import_path_init_api_args="dedoc.api.api_args",

    # ----------------------------------------TABLE RECOGNIZER DEBUG SETTINGS-------------------------------------------
    # path to save debug images for tables recognizer
    path_detect=os.path.join(os.path.abspath(os.sep), "tmp", "dedoc", "debug_tables", "imgs", "detect_lines"),

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
    def get_instance(cls: "Configuration") -> "Configuration":
        """
        Actual object creation will happen when we use Configuration.getInstance()
        """
        if not cls.__instance:
            cls.__instance = Configuration()

        return cls.__instance

    def get_config(self) -> dict:
        if self.__config is None:
            self.__config = _config
        return self.__config


def get_config() -> dict:
    return Configuration.get_instance().get_config()
