import os

__was_called = [False]

_config = [dict(
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

)]


def get_config() -> dict:
    __was_called[0] = True
    return _config[0]


def set_config(config: dict):
    if __was_called[0]:
        raise Exception("Config changed after application start, application may be inconsistent")
    _config[0] = config
