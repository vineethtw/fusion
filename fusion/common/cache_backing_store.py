import cPickle as pickle
import calendar
import json
import os
import pylibmc
import redis
import time

from fusion.common.timeutils import json_handler
from fusion.openstack.common import log as logging
from oslo.config import cfg
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)

REDIS = "redis"
MEMCACHE = "memcache"
FILE_SYSTEM = "filesystem"
REDIS_CLIENT = None
MEMCACHE_CLIENT = None

try:
    REDIS_CLIENT = redis.from_url(
        cfg.CONF.cache.redis_connection_string)
except StandardError as exc:
    logger.warn("Error connecting to Redis: %s", exc)
except NoSuchOptError as exc:
    logger.warn("Redis configuration not found!")

try:
    servers = cfg.CONF.cache.memcache_servers
    MEMCACHE_CLIENT = pylibmc.Client(servers, behaviors={
        "tcp_nodelay": True, "ketama": True}, binary=True)
except StandardError as exc:
    logger.warn("Error connecting to memcache: %s", exc)
except NoSuchOptError as exc:
    logger.warn("Memcache configuration not found!")


class BackingStore(object):
    @staticmethod
    def create(type, max_age):
        if type == REDIS:
            return RedisBackingStore(max_age, REDIS_CLIENT)
        elif type == MEMCACHE:
            return MemcacheBackingStore(max_age, MEMCACHE_CLIENT)
        elif type == FILE_SYSTEM:
            return FileSystemBackingStore(max_age)
        else:
            return None

    def __init__(self, max_age):
        self._max_age = max_age

    def cache(self, key, data):
        logger.warn("Cache.update_cache called with cache_key %s, "
                    "but was not implemented", key)

    def retrieve(self, key):
        logger.warn("Cache.try_cache called with cache_key %s, but was not "
                    "implemented", key)


class RedisBackingStore(BackingStore):
    def __init__(self, max_age, redis_client):
        self._redis_client = redis_client
        super(RedisBackingStore, self).__init__(max_age)

    def cache(self, key, data):
            try:
                self._redis_client.setex(key, self._encode(data),
                                         self._max_age)
            except ConnectionError as exc:
                logger.warn("Error connecting to Redis: %s", exc)
            except Exception as exc:
                logger.warn("Error storing value in redis backing store: %s",
                            exc)

    def retrieve(self, key):
        try:
            value = self._redis_client[key]
            return self._decode(value)
        except ConnectionError as exc:
            logger.warn("Error connecting to Redis: %s", exc)
        except KeyError:
            pass
        except Exception as exc:
            logger.warn("Error accesing redis backing store: %s", exc)
        return None

    @staticmethod
    def _encode(data):
        """Encode python data into format we can restore from Redis."""
        return pickle.dumps(data, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _decode(data):
        """Decode our python data from the Redis string."""
        return pickle.loads(data)


class FileSystemBackingStore(BackingStore):
    def __init__(self, max_age):
        self._cache_root = cfg.CONF.cache.cache_root
        super(FileSystemBackingStore, self).__init__(max_age)

    def retrieve(self, key):
        if not self._expired(key):
            try:
                with open(self._cache_file(key), 'r') as cache:
                    contents = cache.read()
                return json.loads(contents)
            except IOError:
                logger.warn("Error reading disk cache", exc_info=True)

    def cache(self, key, data):
        if not os.path.exists(self._cache_root):
            try:
                os.makedirs(self._cache_root, 0o766)
            except (OSError, IOError):
                logger.warn("Could not create cache directory", exc_info=True)
                return
        try:
            with open(self._cache_file(key), 'w') as cache:
                cache.write(json.dumps(data, default=json_handler))
        except IOError:
            logger.warn("Error updating disk cache", exc_info=True)

    def _cache_file(self, cache_key):
        return os.path.join(self._cache_root, ".%s_cache" % cache_key)

    def _expired(self, cache_key):
        if os.path.exists(self._cache_file(cache_key)):
            cache_last_update_time = os.path.getmtime(
                self._cache_file(cache_key))
            return time.time() - cache_last_update_time >= self._max_age
        return True


class MemcacheBackingStore(BackingStore):
    def __init__(self, max_age, memcache_client):
        self.memcache_client = memcache_client
        super(MemcacheBackingStore, self).__init__(max_age)

    def retrieve(self, key):
        try:
            data = self.memcache_client.get(key)
            if data:
                if calendar.timegm(time.gmtime()) - data[0] < self._max_age:
                    return data[1]
                else:
                    self.memcache_client.delete(key)
        except pylibmc.Error as exc:
            logger.warn("Error while retrieving value from memcache: %s", exc)
        except Exception as exc:
            logger.warn("Error accesing memcache backing store: %s", exc)

    def cache(self, key, data):
        try:
            birthday = calendar.timegm(time.gmtime())
            self.memcache_client.set(key, (birthday, data))
        except pylibmc.Error as exc:
            logger.warn("Error while retrieving value from memcache: %s", exc)
        except Exception as exc:
            logger.warn("Error accesing memcache backing store: %s", exc)
