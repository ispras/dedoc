class ConfigError(Exception):
    ...


class UnavailableModuleError(ConfigError):
    ...


class RuntimeConfigError(ConfigError):
    ...
