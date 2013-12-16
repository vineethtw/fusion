import mock
import unittest
import pylibmc

from fusion.common.cache_backing_store import (
    FileSystemBackingStore,
    RedisBackingStore,
    MemcacheBackingStore)
from redis.exceptions import ConnectionError
from oslo.config import cfg


class FileSystemBackingStoreTest(unittest.TestCase):
    def setUp(self):
        cfg.CONF.reset()
        self.cache_root = "/cache"
        cfg.CONF = mock.Mock(cache=mock.Mock(cache_root=self.cache_root))
        self.cache_file_path = "%s/.get_templates_cache" % self.cache_root

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_retrieve_for_existing_key(self, mock_path_exists, mock_open):
        mock_path_exists.return_value = True
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_file_handle.read.return_value = \
            "\x80\x02}q\x01U\x03fooq\x02U\x03barq\x03s."

        store = FileSystemBackingStore(60)
        result = store.retrieve("get_templates")
        self.assertDictEqual(result, {"foo": "bar"})

        mock_path_exists.assert_called_once_with(self.cache_file_path)
        self.assertTrue(mock_file_handle.read.called)
        mock_open.assert_called_once_with("/cache/.get_templates_cache", "r")

    @mock.patch('os.path.exists')
    def test_retrieve_for_invalid_key(self, mock_path_exists):
        mock_path_exists.return_value = False

        store = FileSystemBackingStore(60)
        self.assertRaises(KeyError, store.retrieve, "get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_retrieve_io_exc_handling(self, mock_path_exists, mock_open):
        mock_path_exists.return_value = True
        mock_open.side_effect = IOError()

        store = FileSystemBackingStore(60)
        store.retrieve("get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)

    @mock.patch('__builtin__.open')
    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_cache_for_no_root(self, mock_path_exists, mock_makedirs,
                               mock_open):
        mock_path_exists.return_value = False
        mock_file_handle = mock_open.return_value.__enter__.return_value

        store = FileSystemBackingStore(60)
        store.cache("get_templates", {"foo": "bar"})

        mock_makedirs.assert_called_once_with(self.cache_root, 0o766)
        mock_file_handle.write.assert_called_once_with(
            '\x80\x02}q\x01U\x03fooq\x02U\x03barq\x03s.')

    @mock.patch('__builtin__.open')
    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_cache_for_existing_root(self, mock_path_exists, mock_makedirs,
                                     mock_open):
        mock_path_exists.return_value = True
        mock_file_handle = mock_open.return_value.__enter__.return_value

        store = FileSystemBackingStore(60)
        store.cache("get_templates", {"foo": "bar"})

        self.assertFalse(mock_makedirs.called)
        mock_file_handle.write.assert_called_once_with(
            '\x80\x02}q\x01U\x03fooq\x02U\x03barq\x03s.')

    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_cache_create_root_exc_handling(self, mock_path_exists,
                                            mock_makedirs):
        mock_path_exists.return_value = False
        mock_makedirs.side_effect = IOError()

        store = FileSystemBackingStore(60)
        store.cache("get_templates", {"foo": "bar"})

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_cache_file_open_exc_handling(self, mock_path_exists, mock_open):
        mock_path_exists.return_value = True
        mock_open.side_effect = IOError()

        store = FileSystemBackingStore(60)
        store.cache("get_templates", {"foo": "bar"})

    @mock.patch('os.path.exists')
    def test_exists(self, mock_path_exists):
        mock_path_exists.return_value = True
        store = FileSystemBackingStore(60)

        self.assertTrue(store.exists("get_templates"))
        self.assertTrue(mock_path_exists.called)

    @mock.patch('os.path.exists')
    def test_exists_for_invalid_path(self, mock_path_exists):
        mock_path_exists.return_value = False
        store = FileSystemBackingStore(60)

        self.assertFalse(store.exists("get_templates"))
        self.assertTrue(mock_path_exists.called)


class RedisBackingStoreTest(unittest.TestCase):
    def test_retrieve(self):
        client = mock.Mock()
        client.get.return_value = "\x80\x02K\nU\rget_templatesq\x01\x86q\x02."

        store = RedisBackingStore(60, client)
        result = store.retrieve("get_templates")
        self.assertEqual((10, "get_templates"), result)
        client.get.assert_called_once_with("get_templates")

    def test_retrieve_for_invalid_key(self):
        client = mock.Mock()
        client.get.return_value = None

        store = RedisBackingStore(60, client)
        self.assertRaises(KeyError, store.retrieve, "get_templates")

        client.get.assert_called_once_with("get_templates")

    def test_retrieve_conn_exc_handling(self):
        client = mock.Mock()
        client.get.side_effect = ConnectionError()

        store = RedisBackingStore(60, client)
        self.assertEqual(None, store.retrieve("get_templates"))

    def test_retrieve_generic_exc_handling(self):
        client = mock.Mock()
        client.get.side_effect = Exception()

        store = RedisBackingStore(60, client)
        self.assertEqual(None, store.retrieve("get_templates"))

    def test_cache(self):
        mock_client = mock.Mock()
        store = RedisBackingStore(60, mock_client)
        store.cache("get_templates", "content")

        mock_client.set.assert_called_once_with(
            "get_templates", "\x80\x02U\x07contentq\x01.")

    def test_cache_exc_handling(self):
        mock_client = mock.Mock()
        mock_client.set.side_effect = Exception("message")
        store = RedisBackingStore(60, mock_client)
        store.cache("get_templates", "content")

    def test_exists(self):
        client = mock.Mock()
        client.exists.return_value = True

        store = RedisBackingStore(60, client)

        self.assertTrue(store.exists("get_templates"))
        client.exists.assert_called_once_with("get_templates")


class MemcacheBackingStoreTest(unittest.TestCase):
    def test_retrieve(self):
        client = mock.Mock()
        client.get.return_value = (10, "content")

        store = MemcacheBackingStore(60, client)
        result = store.retrieve("get_templates")

        self.assertEqual((10, "content"), result)
        client.get.assert_called_once_with("get_templates")

    def test_retrieve_for_invalid_key(self):
        client = mock.Mock()
        client.get.return_value = None

        store = MemcacheBackingStore(5, client)
        self.assertRaises(KeyError, store.retrieve, "get_templates")

        client.get.assert_called_once_with("get_templates")

    def test_retrieve_pylib_exc_handling(self):
        client = mock.Mock()
        client.get.side_effect = pylibmc.Error()

        store = MemcacheBackingStore(5, client)
        result = store.retrieve("get_templates")

        self.assertIsNone(result)

    def test_retrieve_generic_exc_handling(self):
        client = mock.Mock()
        client.get.side_effect = Exception("error")

        store = MemcacheBackingStore(5, client)
        result = store.retrieve("get_templates")

        self.assertIsNone(result)

    def test_cache(self):
        client = mock.Mock()

        store = MemcacheBackingStore(60, client)
        store.cache("get_templates", "content")

        client.set.assert_called_with("get_templates", "content")

    def test_cache_pylibmc_exc_handling(self):
        client = mock.Mock()
        client.set.side_effect = pylibmc.Error()

        store = MemcacheBackingStore(60, client)
        store.cache("get_templates", "content")

    def test_cache_pylibmc_exc_handling(self):
        client = mock.Mock()
        client.set.side_effect = Exception("msg")

        store = MemcacheBackingStore(60, client)
        store.cache("get_templates", "content")

    def test_exists(self):
        client = mock.Mock()
        client.get.return_value = (10, "value")

        store = MemcacheBackingStore(60, client)
        self.assertTrue(store.exists("get_templates"))

        client.get.assert_called_once_with("get_templates")

    def test_exists_for_invalid_key(self):
        client = mock.Mock()
        client.get.return_value = None

        store = MemcacheBackingStore(60, client)
        self.assertFalse(store.exists("get_templates"))

        client.get.assert_called_once_with("get_templates")
