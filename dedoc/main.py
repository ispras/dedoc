from dedoc.api.dedoc_api import get_api, run_api  # noqa
from dedoc.config import Configuration


if __name__ == "__main__":
    Configuration.get_instance().get_config()
    run_api(get_api())
