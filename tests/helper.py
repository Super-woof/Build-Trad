import os, json

from src.interface import Config


def load_test_conf() -> Config:
    path_to_test_conf = "tests/TestSubTraductorV3.conf"
    with open(os.path.join(os.path.curdir, path_to_test_conf), 'r', encoding="utf-8") as file:
        json_data = json.load(file)
        config = Config(**json_data)
    
    return config
    