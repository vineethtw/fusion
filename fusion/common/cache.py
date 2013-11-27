import json
import os

from fusion.openstack.common import log as logging

logger = logging.getLogger(__name__)


class Cache(object):
    def __init__(self, config, timeout):
        self.max_age = timeout if timeout else config.default_cache_timeout

    def __call__(self, func):
        cache_key = func.__name__

        def wrapped_f(*args, **kwargs):
            result = self.try_cache(cache_key)
            if not result:
                result = func(*args, **kwargs)
                self.update_cache(cache_key, result)
            return result

        return wrapped_f

    def try_cache(self, cache_key):
        logger.warn("Cache.try_cache called with cache_key %s, but was not "
                    "implemented", cache_key)

    def update_cache(self, cache_key, data):
        logger.warn("Cache.update_cache called with cache_key %s, "
                    "but was not implemented", cache_key)


class FileSystemCache(Cache):
    def __init__(self, config, timeout):
        self._cache_root = config.cache_root
        super(FileSystemCache, self).__init__(config, timeout)

    def try_cache(self, cache_key):
        if os.path.exists(self._cache_file(cache_key)):
            try:
                with open(self._cache_file(cache_key), 'r') as cache:
                    contents = cache.read()
                return json.loads(contents)
            except IOError:
                logger.warn("Error reading disk cache", exc_info=True)

    def update_cache(self, cache_key, data):
        if not os.path.exists(self._cache_root):
            try:
                os.makedirs(self._cache_root, 0o766)
            except (OSError, IOError):
                logger.warn("Could not create cache directory", exc_info=True)
                return
        try:
            with open(self._cache_file(cache_key), 'w') as cache:
                cache.write(json.dumps(data, default=json_handler))
        except IOError:
            logger.warn("Error updating disk cache", exc_info=True)

    def _cache_file(self, cache_key):
        return os.path.join(self._cache_root, ".%s_cache" % cache_key)

def json_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj
