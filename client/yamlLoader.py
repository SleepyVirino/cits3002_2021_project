import yaml


class YamlLoader():
    def __init__(self):
        pass

    def load(self, path="client.yaml"):
        with open(path) as f:
            data = yaml.load(f,yaml.FullLoader)
        return data


if __name__ == "__main__":
    yamlLoader = YamlLoader()
    data = yamlLoader.load()
    print(data)
