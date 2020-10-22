
class ConfigurationManager(object):
    """
    Pattern Singleton for configuration service
    INFO: Configuration class and config are created once at the first call
    """
    __instance = None
    __config = None

    @classmethod
    def getInstance(cls) -> "ConfigurationManager":
        """
        Actual object creation will happen when we use ConfigurationManager.getInstance()
        """
        if not cls.__instance:
            cls.__instance = ConfigurationManager()

        return cls.__instance

    def __initConfig(self, new_config: dict = None):
        if new_config is None:
            from dedoc.manager_config import _config
            self.__config = _config
        else:
            self.__config = new_config

    def getConfig(self) -> dict:
        if self.__config is None:
            self.__initConfig()
        return self.__config


def get_manager_config():
    return ConfigurationManager().getConfig()
