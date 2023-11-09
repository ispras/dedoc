import importlib.util
import logging
import os
import sys
from typing import Any, Optional

import GPUtil

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s - %(pathname)s - %(levelname)s - %(message)s")

DEBUG_MODE = False
RESOURCES_PATH = os.environ.get("RESOURCES_PATH", os.path.join(os.path.expanduser("~"), ".cache", "dedoc", "resources"))

_config = dict(
    # -----------------------------------------RESOURCES PATH SETTINGS----------------------------------------------------
    resources_path=RESOURCES_PATH,
    intermediate_data_path=os.path.join(RESOURCES_PATH, "datasets"),

    # -----------------------------------------COMMON DEBUG SETTINGS----------------------------------------------------
    debug_mode=DEBUG_MODE,
    path_debug=os.path.join(os.path.abspath(os.sep), "tmp", "dedoc"),

    # --------------------------------------------JOBLIB SETTINGS-------------------------------------------------------
    # number of parallel jobs in some tasks as OCR
    n_jobs=1,

    # --------------------------------------------GPU SETTINGS-------------------------------------------------------
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

    # ----------------------------------------TABLE RECOGNIZER SETTINGS-------------------------------------------------
    min_h_cell=8,
    min_w_cell=20,
    type_top_attr=1,
    type_left_top_attr=2,
    type_left_attr=3,
    max_vertical_extended=20,
    minimal_cell_cnt_line=5,
    minimal_cell_avg_length_line=10,

    path_cells=os.path.join(os.path.abspath(os.sep), "tmp", "dedoc", "debug_tables", "imgs", "cells"),
    path_detect=os.path.join(os.path.abspath(os.sep), "tmp", "dedoc", "debug_tables", "imgs", "detect_lines"),
    rotate_threshold=0.3,

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

    def __init_config(self, args: Optional[Any] = None) -> None:
        if args is not None and args.config_path is not None:
            spec = importlib.util.spec_from_file_location("config_module", args.config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            self.__config = config_module._config
        else:
            self.__config = _config

        gpus = GPUtil.getGPUs()
        if self.__config.get("on_gpu", False) and len(gpus) == 0:
            logger = self.__config.get("logger", logging.getLogger())
            logger.warning("No gpu device available! Changing configuration on_gpu to False!")
            self.__config["on_gpu"] = False

    def get_config(self, args: Optional[Any] = None) -> dict:
        if self.__config is None or args is not None:
            self.__init_config(args)
        return self.__config


def get_config(args: Optional[Any] = None) -> dict:
    return Configuration.get_instance().get_config(args)
