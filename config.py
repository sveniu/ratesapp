import os

class DBConfig(dict):
    def __getitem__(self, key):
        if key == "name":
            return os.environ["DB_NAME"]
        if key == "user":
            return os.environ["DB_USER"]
        if key == "host":
            return os.environ["DB_HOST"]
        raise KeyError(key)

DB = DBConfig()
