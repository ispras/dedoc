from dedoc_future.abstract.module import AbstractModule
from dedoc_future.errors.config import ConfigError


class ModuleRegistry:
    def __init__(self):
        self._name2module: dict[str, type[AbstractModule]] = {}

    def register(self, module: type[AbstractModule]) -> None:
        if module.name in self._name2module:
            raise ConfigError(f"Duplicate module name: {module.name}")
        self._name2module[module.name] = module

    def get(self, name: str) -> type[AbstractModule]:
        if name not in self._name2module:
            raise ConfigError(f"Module not found: {name}")
        return self._name2module[name]

    @property
    def available_modules(self) -> tuple[str, ...]:
        return tuple(k for k, v in self._name2module.items() if v.is_available())
