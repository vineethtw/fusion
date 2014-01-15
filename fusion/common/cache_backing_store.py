import cPickle as pickle
import os
import pylibmc
import redis

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

    def exists(self, key):
        logger.warn("Cache.try_cache called with key %s, but was not "
                    "implemented", key)

    @staticmethod
    def encode(data):
        """Encode python data into format we can restore from Redis."""
        return pickle.dumps(data, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def decode(data):
        """Decode our python data from the Redis string."""
        return pickle.loads(data)


class RedisBackingStore(BackingStore):
    def __init__(self, max_age, redis_client):
        self._redis_client = redis_client
        super(RedisBackingStore, self).__init__(max_age)

    def exists(self, key):
        return self._redis_client.exists(key)

    def cache(self, key, data):
        try:
            self._redis_client.set(key, self.encode(data))
        except ConnectionError as exc:
            logger.warn("Error connecting to Redis: %s", exc)
        except Exception as exc:
            logger.warn("Error storing value in redis backing store: %s",
                        exc)

    def retrieve(self, key):
        try:
            result = self._redis_client.get(key)
        except ConnectionError as exc:
            logger.warn("Error connecting to Redis: %s", exc)
            return None
        except Exception as exc:
            logger.warn("Error accesing redis backing store: %s", exc)
            return None
        if result:
            return self.decode(result)
        else:
            raise KeyError("Key %s not found" % key)


class FileSystemBackingStore(BackingStore):
    def __init__(self, max_age):
        self._cache_root = cfg.CONF.cache.cache_root
        super(FileSystemBackingStore, self).__init__(max_age)

    def retrieve(self, key):
        if self.exists(key):
            try:
                with open(self._cache_file(key), 'r') as cache:
                    contents = cache.read()
                return self.decode(contents)
            except IOError:
                logger.warn("Error reading disk cache", exc_info=True)
        else:
            raise KeyError("Key %s not found" % key)

    def cache(self, key, data):
        if not os.path.exists(self._cache_root):
            try:
                os.makedirs(self._cache_root, 0o766)
            except (OSError, IOError):
                logger.warn("Could not create cache directory", exc_info=True)
                return
        try:
            with open(self._cache_file(key), 'w') as cache:
                cache.write(self.encode(data))
        except IOError:
            logger.warn("Error updating disk cache", exc_info=True)

    def _cache_file(self, cache_key):
        return os.path.join(self._cache_root, ".%s_cache" % cache_key)

    def exists(self, key):
        return os.path.exists(self._cache_file(key))


class MemcacheBackingStore(BackingStore):
    def __init__(self, max_age, memcache_client):
        self.memcache_client = memcache_client
        super(MemcacheBackingStore, self).__init__(max_age)

    def cache(self, key, data):
        try:
            self.memcache_client.set(key, data)
        except pylibmc.Error as exc:
            logger.warn("Error while retrieving value from memcache: %s", exc)
        except Exception as exc:
            logger.warn("Error accesing memcache backing store: %s", exc)

    def exists(self, key):
        try:
            data = self.retrieve(key)
            if data:
                return True
            else:
                return False
        except KeyError:
            return False

    def retrieve(self, key):
        try:
            data = self.memcache_client.get(key)
        except pylibmc.Error as exc:
            logger.warn("Error while retrieving value from memcache: %s",
                        exc)
            return None
        except Exception as exc:
            logger.warn("Error accesing memcache backing store: %s", exc)
            return None
        if data:
            return data
        else:
            raise KeyError("Key %s not found" % key)
