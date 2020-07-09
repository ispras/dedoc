import os
import importlib.util
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config_path", help="path to configuration file")
args = parser.parse_args()

_config = dict(
    # JOBLIB SETTINGS
    # number of parallel jobs in some tasks as OCR
    n_jobs=4,

    # API SETTINGS
    # max file size in bytes
    max_content_length=512 * 1024 * 1024,
    # application port
    api_port=int(os.environ.get('DOCREADER_PORT', '1231')),
    static_files_dirs={}
    #

    # path to external static files (you may get file from this directory with url
    # host:port/xturnal_file?fname=<filename>
    # for example if you want send files from /tmp/dedoc directory uncomment the line below
    # external_static_files_path="/tmp/dedoc",

)


class Configuration(object):
    """
    Pattern Singleton for configuration service
    INFO: Configuration class and config are created once at the first call
    """
    __instance = None
    __config = None

    @classmethod
    def getInstance(cls) -> "Configuration":
        """
        Actual object creation will happen when we use Configuration.getInstance()
        """
        if not cls.__instance:
            cls.__instance = Configuration()

        return cls.__instance

    def __initConfig(self):
        if args.config_path is not None:
            spec = importlib.util.spec_from_file_location("config_module", args.config_path)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            self.__config = config_module._config
        else:
            self.__config = _config

    def getConfig(self) -> dict:
        if self.__config is None:
            self.__initConfig()
        return self.__config


def get_config():
    return Configuration().getConfig()
