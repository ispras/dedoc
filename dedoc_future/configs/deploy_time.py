from pydantic import RootModel

from dedoc_future.abstract import ImmutableBaseModel


class CommonDeployConfig(ImmutableBaseModel, RootModel):
    """
    TODO deploy config validation for each module using ModuleRegistry
    """
    root_module: str
    root: dict[str, ImmutableBaseModel | RootModel] = {}
