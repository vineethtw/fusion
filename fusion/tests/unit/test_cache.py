import calendar

import mock
from eventlet.green import threading
import unittest

from fusion.common import cache
from fusion.common.cache import BACKGROUND_REFRESH
from fusion.common.cache_backing_store import BackingStore, MEMCACHE
from oslo.config import cfg


class CacheTests(unittest.TestCase):

    def setUp(self):
        cfg.CONF.__contains__ = mock.MagicMock(return_value=True)
        BACKGROUND_REFRESH.clear()

    @mock.patch.object(calendar, "timegm")
    def test_in_memory_cache_hit(self, mock_timegm):
        _func = mock.Mock(__name__="key")
        mock_timegm.return_value = 20
        _cache = cache.Cache(timeout=120, store={"key": (10, "data")})
        _cache.get_hash = mock.Mock(return_value="key")
        _wrapped_func = _cache(_func)
        result = _wrapped_func()

        self.assertEquals(result, "data")
        self.assertTrue(mock_timegm.called)
        self.assertFalse(_func.called)

    @mock.patch.object(BackingStore, 'create')
    @mock.patch.object(calendar, "timegm")
    def test_backend_store_cache_hit(self, mock_timegm, mock_create):
        mock_backing_store = mock_create.return_value
        mock_backing_store.exists.return_value = True
        mock_backing_store.retrieve.side_effect = [(10, "data"), (10, "data")]
        _func = mock.Mock(__name__="key")
        mock_timegm.return_value = 20

        in_memory_store = {}
        _cache = cache.Cache(timeout=120, store=in_memory_store,
                             backing_store=MEMCACHE)
        _cache.get_hash = mock.Mock(return_value="key")
        _wrapped_func = _cache(_func)
        result = _wrapped_func()

        self.assertEquals(result, "data")
        self.assertEqual((10, "data"), in_memory_store["key"])
        self.assertTrue(mock_timegm.called)
        self.assertFalse(_func.called)
        mock_create.assert_called_once_with(MEMCACHE, 120)
        mock_backing_store.exists.assert_called_once_with("key")
        mock_backing_store.retrieve.assert_has_calls([
            mock.call('key'),
            mock.call('key')
        ])

    @mock.patch.object(BackingStore, 'create')
    @mock.patch.object(calendar, "timegm")
    def test_cache_miss(self, mock_timegm, mock_create):
        mock_backing_store = mock_create.return_value
        mock_backing_store.exists.return_value = False
        _func = mock.Mock(__name__="key", return_value="data")
        mock_timegm.return_value = 20

        in_memory_store = {}
        _cache = cache.Cache(timeout=120, store=in_memory_store,
                             backing_store=MEMCACHE)
        _cache.get_hash = mock.Mock(return_value="key")
        _wrapped_func = _cache(_func)
        result = _wrapped_func()

        self.assertEquals(result, "data")
        self.assertEqual((20, "data"), in_memory_store["key"])
        self.assertTrue(mock_timegm.called)
        mock_create.assert_called_once_with(MEMCACHE, 120)
        mock_backing_store.exists.assert_called_once_with("key")
        mock_backing_store.cache.assert_called_once_with("key", (20, "data"))

    @mock.patch.object(calendar, "timegm")
    def test_expired_cache_triggers_background_refresh(self, mock_timegm):
        _func = mock.Mock(__name__="key")
        mock_timegm.return_value = 200

        in_memory_store = {"key": (10, "data")}
        _cache = cache.Cache(timeout=120, store=in_memory_store)
        _cache.get_hash = mock.Mock(return_value="key")
        _cache.start_background_refresh = mock.Mock()
        _wrapped_func = _cache(_func)
        result = _wrapped_func()

        self.assertEquals(result, "data")
        self.assertTrue(mock_timegm.called)
        self.assertFalse(_func.called)
        _cache.start_background_refresh.assert_called_once_with("key",
                                                                _func, (), {})

    def test_caching_disabled_when_cache_conf_not_available(self):
        def look_for_cache_conf(*args, **kwargs):
            return False if args[0] == "cache" else True

        cfg.CONF.reset()
        cfg.CONF = mock.Mock()
        cfg.CONF.__contains__ = mock.Mock(side_effect=look_for_cache_conf)
        unwrapped_function = mock.Mock()
        _cache = cache.Cache()
        returned_function = _cache(unwrapped_function)
        self.assertEqual(returned_function, unwrapped_function)

    @mock.patch('eventlet.spawn_n')
    @mock.patch.object(threading, 'Lock')
    def test_start_background_refresh(self, mock_lock, mock_spawn):
        lock = mock_lock.return_value
        _func = mock.Mock(__name__="key")

        _cache = cache.Cache(timeout=120, store={})
        _cache.start_background_refresh("key", _func, (), {})

        self.assertDictEqual(BACKGROUND_REFRESH, {
            'key': {
                'background_thread': mock_spawn.return_value,
                'refresh_lock': lock
            }
        })
        lock.acquire.assert_called_once_with(False)
        mock_spawn.assert_called_once_with(_cache.refresh_cache, "key",
                                           _func, (), {})
        self.assertTrue(lock.release.called)

    @mock.patch('eventlet.spawn_n')
    @mock.patch.object(threading, 'Lock')
    def test_start_background_refresh_exc_handling(self, mock_lock,
                                                   mock_spawn):
        lock = mock_lock.return_value
        _func = mock.Mock(__name__="key")
        mock_spawn.side_effect = StandardError()

        _cache = cache.Cache(timeout=120, store={})
        _cache.start_background_refresh("key", _func, (), {})

        self.assertDictEqual(BACKGROUND_REFRESH, {
            'key': {
                'background_thread': None,
                'refresh_lock': lock
            }
        })
        lock.acquire.assert_called_once_with(False)
        self.assertTrue(lock.release.called)
