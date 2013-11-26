import mock
import unittest

from fusion.common.cache import FileSystemCache


class FileSystemCacheTest(unittest.TestCase):
    @mock.patch('json.loads')
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_try_cache(self, mock_path_exists, mock_open, mock_json_load):
        mock_path_exists.return_value = True
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_file_handle.read.return_value = "contents"
        mock_config = mock.Mock(cache_root="/cache")

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.try_cache("get_templates")

        mock_path_exists.assert_called_once_with(
            "/cache/.get_templates_cache")
        self.assertTrue(mock_file_handle.read.called)
        mock_json_load.assert_called_once_with("contents")
        mock_open.assert_called_once_with("/cache/.get_templates_cache", "r")

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_try_cache_exc_handling(self, mock_path_exists, mock_open):
        mock_path_exists.return_value = True
        mock_open.side_effect = IOError("error")
        mock_config = mock.Mock(cache_root="/cache")

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.try_cache("get_templates")

        mock_path_exists.assert_called_once_with(
            "/cache/.get_templates_cache")

    @mock.patch('json.dumps')
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_update_cache(self, mock_path_exists, mock_open, mock_json_dumps):
        mock_path_exists.return_value = True
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_config = mock.Mock(cache_root="/cache")
        mock_json_dumps.return_value = {"foo": "bar"}

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.update_cache("get_templates", '{"foo": "bar"}')

        mock_path_exists.assert_called_once_with("/cache")
        self.assertTrue(mock_file_handle.write.called)
        mock_json_dumps.assert_called_once_with('{"foo": "bar"}')
        mock_open.assert_called_once_with("/cache/.get_templates_cache", "w")
        mock_file_handle.write.assert_called_once_with({"foo": "bar"})

    @mock.patch('os.makedirs')
    @mock.patch('json.dumps')
    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_update_cache_for_missing_root(self, mock_path_exists,
                                           mock_open, mock_json_dumps,
                                           mock_makedirs):
        mock_path_exists.return_value = False
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_config = mock.Mock(cache_root="/cache")
        mock_json_dumps.return_value = {"foo": "bar"}

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.update_cache("get_templates", '{"foo": "bar"}')

        mock_path_exists.assert_called_once_with("/cache")
        self.assertTrue(mock_file_handle.write.called)
        mock_json_dumps.assert_called_once_with('{"foo": "bar"}')
        mock_open.assert_called_once_with("/cache/.get_templates_cache", "w")
        mock_file_handle.write.assert_called_once_with({"foo": "bar"})
        mock_makedirs.assert_called_once_with("/cache", 0o766)

    @mock.patch('os.makedirs')
    @mock.patch('os.path.exists')
    def test_update_cache_root_create_exc_handling(self, mock_path_exists,
                                                   mock_makedirs):
        mock_path_exists.return_value = False
        mock_makedirs.side_effect = IOError()
        mock_config = mock.Mock(cache_root="/cache")

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.update_cache("get_templates", None)

        mock_path_exists.assert_called_once_with("/cache")

    @mock.patch('__builtin__.open')
    @mock.patch('os.path.exists')
    def test_update_cache_root_create_exc_handling(self, mock_path_exists,
                                                   mock_open):
        mock_path_exists.return_value = True
        mock_config = mock.Mock(cache_root="/cache")
        mock_open.side_effect = IOError()

        fs_cache = FileSystemCache(mock_config, 60)
        fs_cache.update_cache("get_templates", None)

        mock_path_exists.assert_called_once_with("/cache")
