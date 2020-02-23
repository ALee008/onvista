import os
import time
import configparser
import pandas as pd
import multiprocessing
from multiprocessing.pool import ThreadPool
import logging

logger = logging
logger.basicConfig(format='%(levelname)s: %(asctime)s - %(message)s', level=logging.INFO)

# DEFAULT_FMT = '[{elapsed:0.8f}s] {name}({args}) -> {result}'
DEFAULT_FMT = '[{elapsed:0.8f}s] {name}({args})'

# read configurations
config = configparser.ConfigParser()
config.read("onvista.ini")
defaults = config["DEFAULT"]

# if max number of parallel processes = 0, set it to number of available CPU.
if defaults["max_num_processes"]:
    MAX_NUM_PROCESSES = int(defaults["max_num_processes"])
else:
    MAX_NUM_PROCESSES = multiprocessing.cpu_count()

RESOURCES_PATH = defaults["resources_path"]


def clock(fmt=DEFAULT_FMT):
    def decorate(func):
        def clocked(*_args):
            t0 = time.time()
            _result = func(*_args)
            elapsed = time.time() - t0
            name = func.__name__
            args = ', '.join(repr(arg) for arg in _args)
            result = repr(_result)
            print(fmt.format(**locals()))
            return _result
        return clocked
    return decorate


@clock()
def multiprocess(func, list_of_objects: list) -> list:
    """

    :param func: function object which is mapped on all objects of list_of_objects
    :param list_of_objects: self-explanatory
    :return: (list) results of function calls.
    """
    result = list()
    with ThreadPool(MAX_NUM_PROCESSES) as pool:
        for sub_result in pool.map(func, list_of_objects):
            result.append(sub_result)

    return result


def export_df(data: pd.DataFrame, file_name: str) -> None:
    file_path = os.path.join(RESOURCES_PATH, file_name)
    _, extension = os.path.splitext(file_name)
    export = {
        '.html': data.to_html,
        '.json': data.to_json,
        ".xlsx": data.to_excel,
    }
    try:
        export[extension](file_path)
    except KeyError:
        logger(f"{extension} format not supported. Supported extensions: {list(export.keys())}")
        raise

    return None


