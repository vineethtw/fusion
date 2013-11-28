import mock
import unittest

from fusion.common.cache_backing_store import (
    FileSystemBackingStore,
    RedisBackingStore,
    REDIS_CLIENT,
)
from oslo.config import cfg


class FileSystemBackingStoreTest(unittest.TestCase):
    def setUp(self):
        cfg.CONF.reset()
        self.cache_root = "/cache"
        cfg.CONF = mock.Mock(cache=mock.Mock(cache_root=self.cache_root))
        self.cache_file_path = "%s/.get_templates_cache" % self.cache_root

    @mock.patch('json.loads')
    @mock.patch('__builtin__.open')
    @mock.patch('time.time')
    @mock.patch('os.path.getmtime')
    @mock.patch('os.path.exists')
    def test_retrieve_for_existing_cache(self, mock_path_exists,
                                         mock_getmtime, mock_time,
                                         mock_open, mock_json_load):
        mock_path_exists.return_value = True
        mock_getmtime.return_value = 50
        mock_time.return_value = 90
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_file_handle.read.return_value = "contents"

        store = FileSystemBackingStore(60)
        store.retrieve("get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)
        mock_getmtime.assert_called_once_with(self.cache_file_path)
        self.assertTrue(mock_time.called)
        self.assertTrue(mock_file_handle.read.called)
        mock_json_load.assert_called_once_with("contents")
        mock_open.assert_called_once_with("/cache/.get_templates_cache", "r")

    @mock.patch('time.time')
    @mock.patch('os.path.getmtime')
    @mock.patch('os.path.exists')
    def test_retrieve_for_expired_cache(self, mock_path_exists,
                                        mock_getmtime, mock_time):
        mock_path_exists.return_value = True
        mock_getmtime.return_value = 10
        mock_time.return_value = 90

        store = FileSystemBackingStore(60)
        store.retrieve("get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)
        mock_getmtime.assert_called_once_with(self.cache_file_path)
        self.assertTrue(mock_time.called)

    @mock.patch('os.path.exists')
    def test_retrieve_for_no_cache(self, mock_path_exists):
        mock_path_exists.return_value = False

        store = FileSystemBackingStore(60)
        store.retrieve("get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)

    @mock.patch('__builtin__.open')
    @mock.patch('time.time')
    @mock.patch('os.path.getmtime')
    @mock.patch('os.path.exists')
    def test_retrieve_exc_handling(self, mock_path_exists, mock_getmtime,
                                   mock_time, mock_open):
        mock_path_exists.return_value = True
        mock_getmtime.return_value = 50
        mock_time.return_value = 90
        mock_open.side_effect = IOError()

        store = FileSystemBackingStore(60)
        store.retrieve("get_templates")

        mock_path_exists.assert_called_once_with(self.cache_file_path)
        mock_getmtime.assert_called_once_with(self.cache_file_path)
        self.assertTrue(mock_time.called)

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
        mock_file_handle.write.assert_called_once_with('{"foo": "bar"}')

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
        mock_file_handle.write.assert_called_once_with('{"foo": "bar"}')

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


class RedisBackingStoreTest(unittest.TestCase):
    def test_retrieve(self):
        client = {'get_templates': "\x80\x02U\x07contentq\x01."}
        store = RedisBackingStore(60, client)
        result = store.retrieve("get_templates")
        self.assertEqual("content", result)

    def test_cache(self):
        mock_client = mock.Mock()
        store = RedisBackingStore(60, mock_client)
        store.cache("get_templates", "content")
        mock_client.setex.assert_called_once_with("get_templates",
                                                  "\x80\x02U\x07contentq\x01"
                                                  ".", 60)

    def test_cache_exc_handling(self):
        mock_client = mock.Mock()
        mock_client.setex.side_effect = Exception("message")
        store = RedisBackingStore(60, mock_client)
        store.cache("get_templates", "content")
