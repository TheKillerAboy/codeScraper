import yaml

from utils import Path


class Config:
    def __init__(self):
        with open(Path.CONFIG, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

    def __getitem__(self, item):
        return self.config[item]

    def __setitem__(self, key, value):
        self.config[key] = value

    def save(self):
        with open(Path.CONFIG, 'w') as f:
            yaml.dump(self.config, f)