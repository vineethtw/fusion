import json

from fusion.classes import ExtensibleSequence, ExtensibleDict


class TemplateCatalog(ExtensibleSequence):
    def __init__(self, *args, **kwargs):
        self.store = [self.__to_template(x) for x in list(*args)]

    @staticmethod
    def from_json(definition):
        catalog = json.loads(definition)
        return TemplateCatalog(catalog["templates"])

    @staticmethod
    def __to_template(obj):
        if isinstance(obj, TemplateCatalogEntry):
            return obj
        if isinstance(obj, dict):
            return TemplateCatalogEntry(obj)
        raise TypeError("Template cannot be created from : %s", obj.__repr__())

    def size(self):
        return self.__len__()


class TemplateCatalogEntry(ExtensibleDict):
    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))


