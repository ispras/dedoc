import os
import sys
import importlib.util


_config = dict(
    # JOBLIB SETTINGS
    # number of parallel jobs in some tasks as OCR
    n_jobs=4,

    # API SETTINGS
    # max file size in bytes
    max_content_length=512 * 1024 * 1024,
    # application port
    api_port=int(os.environ.get('DOCREADER_PORT', '1231')),
    #

    # path to external static files (you may get file from this directory with url
    # host:port/xturnal_file?fname=<filename>
    # for example if you want send files from /tmp/dedoc directory uncomment the line below
    # external_static_files_path="/tmp/dedoc",

)


def get_config() -> dict:
    if len(sys.argv) == 2:
        config_path = os.path.abspath(sys.argv[-1])
        spec = importlib.util.spec_from_file_location("config_module", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        return config_module._config
    return _config
