
class ConfigurationManager(object):
    """
    Pattern Singleton for configuration service
    INFO: Configuration class and config are created once at the first call
    For initialization ConfigurationManager call ConfigurationManager.getInstance().initConfig(new_config: dict)
    If you need default config, call ConfigurationManager.getInstance()
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

    def initConfig(self, new_config: dict = None):
        if new_config is None:
            from dedoc.manager_config import _config
            self.__instance.__config = _config
        else:
            self.__instance.__config = new_config

    def getConfig(self) -> dict:
        if self.__instance.__config is None:
            self.initConfig()
        return self.__instance.__config


def get_manager_config():
    return ConfigurationManager().getConfig()
