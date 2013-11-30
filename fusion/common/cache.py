import time
import calendar

from fusion.common.cache_backing_store import BackingStore
from fusion.openstack.common import log as logging
from oslo.config import cfg
from fusion.common import config

logger = logging.getLogger(__name__)

class Cache(object):
    def __init__(self, timeout=None, backing_store=None, store=None):
        self._max_age = self.__default_timeout() if not timeout else timeout
        self._store = store or {}
        self._backing_store = BackingStore.create(backing_store,
                                                  self._max_age)
        self.memorized_function = None

    def __default_timeout(self):
        return config.safe_get_config("cache", "default_timeout")

    def __call__(self, func):
        if not self.caching_enabled():
            return func

        self.memorized_function = func.__name__

        def wrapped_f(*args, **kwargs):
            result = self.try_cache(self.memorized_function)
            if not result:
                result = func(*args, **kwargs)
                self.update_cache(self.memorized_function, result)
            return result

        return wrapped_f

    def caching_enabled(self):
        return 'cache' in cfg.CONF

    def try_cache(self, key):
        if key in self._store:
            birthday, data = self._store[key]
            age = calendar.timegm(time.gmtime()) - birthday
            if age < self._max_age:
                logger.debug("Cache hit in %s", self.memorized_function)
                return data
        elif self._backing_store:
            value = self._backing_store.retrieve(key)
            if value:
                self._store[key] = value
        return None

    def update_cache(self, key, value):
        self._store[key] = (calendar.timegm(time.gmtime()), value)
        if self._backing_store:
            self._backing_store.cache(key, value)
