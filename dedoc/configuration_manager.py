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
    def getInstance(cls) -> "ConfigurationManager":  # noqa
        """
        Actual object creation will happen when we use ConfigurationManager.getInstance()
        """
        if not cls.__instance:
            cls.__instance = ConfigurationManager()

        return cls.__instance

    def initConfig(self, config: dict, new_config: dict = None) -> None:
        if new_config is None:
            from dedoc.manager_config import get_manager_config
            self.__instance.__config = get_manager_config(config)
        else:
            self.__instance.__config = new_config

    def getConfig(self, config: dict) -> dict:
        if self.getInstance().__config is None:
            self.initConfig(config)
        return self.__instance.__config


def get_manager_config(config: dict) -> dict:
    return ConfigurationManager().getConfig(config)
