import argparse

from dedoc.api.dedoc_api import get_api, run_api  # noqa
from dedoc.config import Configuration, get_config


def main() -> None:
    run_api(get_api())


if __name__ == "__main__":
    parser_config = argparse.ArgumentParser()
    parser_config.add_argument("-c", "--config_path", help="path to configuration file")
    parser_config.add_argument("-m", "--module", help="Only for tests")
    parser_config.add_argument("-f", "--test_files", metavar="VALUE", nargs="*", help="Only for tests")
    parser_config.add_argument("-v", "--unitest_verbose_mode", nargs="?", help="to enable verbose mode of unittest. Only for tests")

    args_config = parser_config.parse_args()
    Configuration.get_instance().get_config(args_config)
    config = get_config()

    if config.get("labeling_mode", False):
        from api.train_dataset.train_dataset_api import run_special_api  # noqa
        run_special_api()
    else:
        main()
