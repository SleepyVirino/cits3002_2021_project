import yaml


class YamlLoader():
    def __init__(self):
        pass

    @staticmethod
    def load(path="client.yaml"):
        with open(path) as f:
            data = yaml.load(f, yaml.FullLoader)
        return data
