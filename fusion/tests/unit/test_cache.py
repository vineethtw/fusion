import mock
import unittest
import calendar

from fusion.common.cache_backing_store import BackingStore
from fusion.common import cache
from oslo.config import cfg


class CacheTests(unittest.TestCase):

    def setUp(self):
        cfg.CONF.reset()
        cfg.CONF = mock.MagicMock()

    @mock.patch.object(calendar, "timegm")
    def test_cache_cache_hit(self, mock_timegm):
        # current time is within the age
        mock_timegm.return_value = 10
        _cache = cache.Cache(timeout=120, store={"key": (10, "data")})
        returned = _cache.try_cache("key")
        self.assertEquals(returned, "data")

    @mock.patch.object(calendar, "timegm")
    @mock.patch.object(BackingStore, "create")
    def test_in_memory_cache_has_expired_value(
            self, mock_backing_store_create, mock_timegm):
        # current time is way past age
        mock_timegm.return_value = 1000
        mock_backing_store = mock.MagicMock(retrieve=mock.MagicMock(
            return_value="from_backing_store"))
        mock_backing_store_create.return_value = mock_backing_store
        _cache = cache.Cache(timeout=120, store={"key": (10, "data")},
                             backing_store=mock_backing_store)
        returned = _cache.try_cache("key")
        #need to make a fresh call
        self.assertEquals(returned, None)

    @mock.patch('time.gmtime')
    @mock.patch.object(calendar, "timegm")
    @mock.patch.object(BackingStore, "create")
    def test_cache_in_memory_cache_miss_but_backing_store_has_value(
            self, mock_backingstore_create, mock_timegm, mock_gmtime):
        mock_gmtime.side_effect = [10, 20]
        #current time is way past age
        mock_timegm.side_effect = [1000, 1050]
        mock_backing_store = mock.MagicMock(retrieve=mock.MagicMock(
            return_value="from_backing_store"))
        mock_backingstore_create.return_value = mock_backing_store
        _cache = cache.Cache(timeout=120,
                             backing_store=mock_backing_store)
        backend_store_result = _cache.try_cache("key")
        in_memory_result = _cache.try_cache("key")
        self.assertEquals(backend_store_result, "from_backing_store")
        self.assertEquals(in_memory_result, "from_backing_store")
        mock_backing_store.retrieve.assert_called_once_with("key")
        timegm_calls = [mock.call(10), mock.call(20)]
        mock_timegm.assert_has_calls(timegm_calls)

    @mock.patch.object(calendar, "timegm")
    @mock.patch.object(BackingStore, "create")
    def test_inmemory_cache_miss_and_backing_store_does_not_have_value(
            self, mock_backingstore_create, mock_timegm):
        #current time is way past age
        mock_timegm.return_value = 1000
        mock_backing_store = mock.MagicMock(retrieve=mock.MagicMock(
            return_value=None))
        mock_backingstore_create.return_value = mock_backing_store
        _cache = cache.Cache(timeout=120, store={"key": (10, "data")},
                             backing_store=mock_backing_store)
        returned = _cache.try_cache("key")
        self.assertEquals(returned, None)

    def test_caching_disabled_when_cache_conf_not_available(self):
        def look_for_cache_conf(*args, **kwargs):
            return False if args[0] == "cache" else True

        cfg.CONF.__contains__ = mock.Mock(side_effect=look_for_cache_conf)
        unwrapped_function = mock.Mock()
        _cache = cache.Cache()
        returned_function = _cache(unwrapped_function)
        self.assertEqual(returned_function, unwrapped_function)

    def test_cache_call_method_with_a_cache_hit(self):
        cfg.CONF.__contains__ = mock.MagicMock(return_value=True)
        _func = mock.MagicMock(__name__="function_name")
        _cache = cache.Cache()
        _wrapped_func = _cache(_func)

        _cache.try_cache = mock.MagicMock(return_value="cached_data")

        result = _wrapped_func()
        self.assertEquals("cached_data", result)

        _cache.try_cache.assert_called_once_with('function_name')

    @mock.patch.object(calendar, "timegm")
    def test_updates_only_in_memory_cache_when_try_cache_fails(self, timegm):
        cfg.CONF.__contains__ = mock.MagicMock(return_value=True)
        timegm.return_value = "time"
        _func = mock.MagicMock(__name__="function_name",
                               return_value="result_from_a_fresh_call")
        _cache = cache.Cache()
        _wrapped_func = _cache(_func)

        _cache.try_cache = mock.MagicMock(return_value=None)

        result = _wrapped_func()
        self.assertEquals("result_from_a_fresh_call", result)

        self.assertTrue("function_name" in _cache._store)
        self.assertEquals(("time", "result_from_a_fresh_call"),
                          _cache._store["function_name"])
        _cache.try_cache.assert_called_once_with('function_name')

    @mock.patch.object(calendar, "timegm")
    @mock.patch.object(BackingStore, "create")
    def test_update_both_in_memory_cache_and_backingstore_when_try_cache_fails(
            self, backing_store_create, timegm):
        cfg.CONF.__contains__ = mock.MagicMock(return_value=True)
        backing_store = mock.MagicMock()
        backing_store_create.return_value=backing_store
        timegm.return_value = "time"
        _func = mock.MagicMock(__name__="function_name",
                               return_value="result_from_a_fresh_call")
        _cache = cache.Cache()
        _wrapped_func = _cache(_func)

        _cache.try_cache = mock.MagicMock(return_value=None)

        result = _wrapped_func()
        self.assertEquals("result_from_a_fresh_call", result)

        self.assertTrue("function_name" in _cache._store)
        self.assertEquals(("time", "result_from_a_fresh_call"), _cache._store[
            "function_name"])
        _cache.try_cache.assert_called_once_with('function_name')
        backing_store.cache.assert_called_once_with(
            "function_name", "result_from_a_fresh_call")

