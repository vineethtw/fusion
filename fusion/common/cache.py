import time
import calendar

import eventlet
from eventlet.green import threading

from fusion.common.cache_backing_store import BackingStore
from fusion.common import config
from fusion.openstack.common import log as logging
from oslo.config import cfg


logger = logging.getLogger(__name__)

BACKGROUND_REFRESH = {}


class Cache(object):
    def __init__(self, timeout=None, backing_store=None, store=None):
        self._max_age = self.__default_timeout() if not timeout else timeout
        self._store = {} if store is None else store
        self._backing_store = BackingStore.create(backing_store,
                                                  self._max_age)

    def expired(self, key):
        if key in self._store:
            birthday, data = self._store[key]
            age = calendar.timegm(time.gmtime()) - birthday
            return age >= self._max_age
        elif self._backing_store:
            birthday, value = self._backing_store.retrieve(key)
            if value:
                age = calendar.timegm(time.gmtime()) - birthday
                return age >= self._max_age
        return None

    def exists(self, key):
        if key in self._store:
            return True
        else:
            if self._backing_store:
                return self._backing_store.exists(key)
        return False

    def start_background_refresh(self, key, func, args, kwargs):
        background_stats = BACKGROUND_REFRESH.get(key, {})
        background_thread = background_stats.get('background_thread')
        refresh_lock = background_stats.get('refresh_lock', threading.Lock())
        if background_thread is None and refresh_lock.acquire(False):
            try:
                background_thread = eventlet.spawn_n(
                    self.refresh_cache, key, func, args, kwargs)
                logger.debug("Refreshing cache for key %s", key)
            except StandardError:
                background_thread = None
                logger.error("Error initiating cache refresh", exc_info=True)
            finally:
                refresh_lock.release()
                background_stats.update({
                    'background_thread': background_thread,
                    'refresh_lock': refresh_lock
                })
                BACKGROUND_REFRESH[key] = background_stats
        else:
            logger.debug("Cache refresh for key %s is already in progress",
                         key)

    def refresh_cache(self, key, func, args, kwargs):
        result = func(*args, **kwargs)
        self.update_cache(key, result)
        if BACKGROUND_REFRESH.get(key):
            BACKGROUND_REFRESH.get(key)['background_thread'] = None
        logger.debug("Cache refreshed for key %s", key)
        return result

    def __call__(self, func):
        if not self.caching_enabled():
            return func

        def wrapped_f(*args, **kwargs):
            key = self.get_hash(func.__name__, *args, **kwargs)
            if self.exists(key):
                if self.expired(key):
                    self.start_background_refresh(key, func, args, kwargs)
                result = self.get(key)
            else:
                result = self.refresh_cache(key, func, args, kwargs)
            return result

        return wrapped_f

    def caching_enabled(self):
        return 'cache' in cfg.CONF

    def get(self, key):
        if key in self._store:
            logger.debug("[%s] Cache hit for key %s",
                         self.__class__.__name__, key)
            _, data = self._store[key]
            return data
        elif self._backing_store:
            birthday, value = self._backing_store.retrieve(key)
            logger.debug("[%s] Cache hit for key %s",
                         self._backing_store.__class__.__name__, key)
            self._store[key] = (birthday, value)
            return value
        return None

    def update_cache(self, key, value):
        birthday = calendar.timegm(time.gmtime())
        self._store[key] = (birthday, value)
        logger.debug("[%s] Updated cache for key %s",
                     self.__class__.__name__, key)
        if self._backing_store:
            self._backing_store.cache(key, (birthday, value))
            logger.debug("[%s] Updated cache for key %s",
                         self._backing_store.__class__.__name__, key)

    def get_hash(self, func_name, *args, **kwargs):
        return str((func_name, args, tuple(sorted(kwargs.items()))))

    def __default_timeout(self):
        return config.safe_get_config("cache", "default_timeout")
