import yaml

import mock
import unittest

from fusion.api.templates import template_manager as managers
from oslo.config import cfg


class TemplateTests(unittest.TestCase):
    def setUp(self):
        cfg.CONF.reset()
        cfg.CONF = mock.Mock(cache=mock.Mock(cache_root="/cache", timeout=10))

    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_get_catalog(self, get_client):
        client = mock.MagicMock()
        options = mock.MagicMock(
            github=mock.MagicMock(template_catalog_path="catalog_path",
                                  repository_name="repo"))

        mock_repo = mock.MagicMock()
        mock_repo.get_file_contents.return_value = mock.MagicMock(
            content="YmFzZV82NF9zdHJpbmc==")

        mock_user = mock.MagicMock()
        mock_user.get_repo.return_value = mock_repo
        client.get_user.return_value = mock_user
        get_client.return_value = client

        manager = managers.GithubManager(options)
        catalog = manager.get_catalog()

        self.assertEquals("base_64_string", catalog)

        mock_repo.get_file_contents.assert_called_once_with("catalog_path")
        mock_user.get_repo.assert_called_once_with("repo")

    @mock.patch('requests.get')
    @mock.patch.object(managers.GithubManager, 'get_client')
    @mock.patch.object(managers.GithubManager, 'get_catalog')
    def test_get_templates(self, mock_get_catalog, mock_get_client, mock_get):
        mock_get_catalog.return_value = """
        {
            "templates": [
                {
                    "id": 1,
                    "name": "Single Instance Redis Server (Linux)",
                    "url": "https://github.com/templates/redis.template"
                },
                {
                    "id": 2,
                    "name": "Multi-node wordpress",
                    "url": "https://github.com/templates/wordpress.template"
                }
            ]
        }
        """
        redis_template = """
        description: |
            Simple template to deploy Redis on a cloud server
        """
        wordpress_template = """
        description: |
            Simple template to deploy wordpress on a cloud server
        """
        mock_get.side_effect = [mock.Mock(content=redis_template),
                                mock.Mock(content=wordpress_template)]
        mock_options = mock.Mock(github={})

        manager = managers.GithubManager(mock_options)
        templates = manager.get_templates()

        self.assertEqual(2, len(templates))
        self.assertListEqual(templates.keys(), [1, 2])
        self.assertTrue(mock_get_catalog.called)
        self.assertTrue(mock_get_client.called)
        self.assertEqual(templates[1], yaml.load(redis_template))
        self.assertEqual(templates[2], yaml.load(wordpress_template))
        get_calls = [
            mock.call("https://github.com/templates/redis.template"),
            mock.call("https://github.com/templates/wordpress.template"),
        ]
        mock_get.assert_has_calls(get_calls)
