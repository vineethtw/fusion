import collections
import json


class ExtensibleSequence(collections.MutableSequence):
    def __len__(self):
        return len(self.store)

    def __getitem__(self, ii):
        return self.store[ii]

    def __delitem__(self, ii):
        del self.store[ii]

    def __setitem__(self, ii, val):
        return self.store[ii]

    def __str__(self):
        return str(self.store)

    def __repr__(self):
        return str(self.store)

    def insert(self, ii, val):
        self.store.insert(ii, val)

    def append(self, val):
        list_idx = len(self.store)
        self.insert(list_idx, val)

    def dumps(self, *args, **kwargs):
        """Dump json string of this class

        Utility function to use since this is not detected as a dict by json
        """
        if 'default' not in kwargs:
            kwargs['default'] = lambda obj: obj.__dict__
        return json.dumps(self.store, *args, **kwargs)


class ExtensibleDict(collections.MutableMapping):
    def __getattr__(self, name):
        return self.__getitem__(name)

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __keytransform__(self, key):
        return key
