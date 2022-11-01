#  change config and manager config here if you want
# new_config = ...
# new_manager_config = ...
# set_manager_config(new_manager_config)
# set_config(new_config)


# 1 - set configuration of service
from src.configuration_manager import ConfigurationManager

ConfigurationManager().getInstance()

# 2 - run service
from src.api.dedoc_api import run_api, get_api  # noqa

run_api(get_api())
