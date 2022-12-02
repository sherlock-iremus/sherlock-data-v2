from pathlib import Path
import uuid
import yaml


class Cache:
    def __init__(self, path):
        self.path = path
        cache_file = Path(self.path)
        if cache_file.is_file():
            with open(self.path, encoding='utf-8') as f:
                _ = yaml.load(f, Loader=yaml.FullLoader)
                if _:
                    self.cache = _
                else:
                    self.cache = {}
        else:
            self.cache = {}

    def get_uuid(self, key_parts, create=False):
        if not create:
            value = self.cache
            for i in range(len(key_parts)):
                k = key_parts[i]
                if k not in value:
                    raise Exception(f"La clef demandée {str(key_parts)} n'existe pas dans le cache {self.path}.")
                else:
                    if i == len(key_parts) - 1:
                        return value[k]
                value = value[k]
        if not create:
            raise Exception("On ne devrait jamais être ici.")

        value = self.cache
        key_parts = [str(k) for k in key_parts]
        for i in range(len(key_parts)):
            k = key_parts[i]
            if k not in value:
                if i == len(key_parts) - 1:
                    value[k] = str(uuid.uuid4())
                    return value[k]
                else:
                    value[k] = dict()
            else:
                if i == len(key_parts) - 1:
                    return value[k]

            value = value[k]

    def bye(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            yaml.dump(self.cache, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
