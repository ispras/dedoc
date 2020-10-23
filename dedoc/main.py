#  change config and manager config here if you want
# new_config = ...
# new_manager_config = ...
# set_manager_config(new_manager_config)
# set_config(new_config)

from dedoc.api.dedoc_api import run_api, get_api
from dedoc.configuration_manager import ConfigurationManager

# 1 - set configuration of service
ConfigurationManager.getInstance()
# 2 - run service
run_api(get_api())
