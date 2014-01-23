import yaml

import mock
import unittest

from fusion.api.templates import template_manager as managers


class GithubManagerTest(unittest.TestCase):
    @mock.patch('base64.b64decode')
    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_get_templates_without_meta(self, mock_get_client, mock_decode):
        redis_template = """
        description: |
            Simple template to deploy Redis on a cloud server
        version: stable
        id: '1234'
        """
        wordpress_template = """
        description: |
            Simple template to deploy wordpress on a cloud server
        version: stable
        id: '2345'
        """
        github_client = mock_get_client.return_value
        mock_org = github_client.get_organization.return_value
        redis_repo = mock.Mock(id=1234)
        wordpress_repo = mock.Mock(id=2345)
        redis_repo.get_file_contents.return_value = mock.Mock(
            content="redis_template")
        wordpress_repo.get_file_contents.return_value = mock.Mock(
            content="wordpress_template")
        mock_org.get_repos.return_value = [redis_repo, wordpress_repo]
        mock_decode.side_effect = [redis_template, wordpress_template]

        mock_options = mock.Mock(
            github=mock.Mock(api_base="https://api.github.com",
                             organization="heat-templates",
                             metadata_file="heat.metadata",
                             template_file="heat.template"))

        expected_templates = [
            yaml.load(redis_template),
            yaml.load(wordpress_template)
        ]

        manager = managers.GithubManager(mock_options)
        templates = manager.get_templates(['stable'], False)

        self.assertEqual(expected_templates, templates)
        self.assertTrue(mock_get_client.called)
        github_client.get_organization.assert_called_once_with(
            "heat-templates")
        self.assertTrue(mock_org.get_repos.called)
        redis_repo.get_file_contents.assert_called_once_with("heat.template",
                                                             ref="stable")
        wordpress_repo.get_file_contents.assert_called_once_with(
            "heat.template", ref='stable')
        decode_calls = [
            mock.call('redis_template'),
            mock.call('wordpress_template')
        ]
        mock_decode.assert_has_calls(decode_calls)

    @mock.patch('base64.b64decode')
    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_get_templates_with_meta(self, mock_get_client, mock_decode):
        redis_template = """
        description: |
            Simple template to deploy Redis on a cloud server
        version: stable
        id: '1234'
        """
        redis_metadata = """
        meta: |
            Metadata for redis template
        """
        wordpress_template = """
        description: |
            Simple template to deploy wordpress on a cloud server
        version: stable
        id: '2345'
        """

        github_client = mock_get_client.return_value
        mock_org = github_client.get_organization.return_value
        redis_repo = mock.Mock(id=1234)
        wordpress_repo = mock.Mock(id=2345)
        redis_repo.get_file_contents.side_effect = [
            mock.Mock(content="redis_template"),
            mock.Mock(content="redis_metadata"),
        ]
        wordpress_repo.get_file_contents.side_effect = [
            mock.Mock(content="wordpress_template"),
            None
        ]
        mock_org.get_repos.return_value = [redis_repo, wordpress_repo]
        mock_decode.side_effect = [redis_template, redis_metadata,
                                   wordpress_template]

        mock_options = mock.Mock(
            github=mock.Mock(api_base="https://api.github.com",
                             organization="heat-templates",
                             metadata_file="heat.metadata",
                             template_file="heat.template"))
        redis = yaml.load(redis_template)
        redis.update(yaml.load(redis_metadata))

        expected_templates = [
            redis,
            yaml.load(wordpress_template)
        ]

        manager = managers.GithubManager(mock_options)
        templates = manager.get_templates(['stable'], True)

        self.assertEqual(expected_templates, templates)
        self.assertTrue(mock_get_client.called)
        github_client.get_organization.assert_called_once_with(
            "heat-templates")
        self.assertTrue(mock_org.get_repos.called)
        redis_repo_get_file_calls = [
            mock.call('heat.template', ref='stable'),
            mock.call('heat.metadata', ref='stable'),
        ]
        wordpress_repo_get_file_calls = [
            mock.call('heat.template', ref='stable'),
            mock.call('heat.metadata', ref='stable'),
        ]
        redis_repo.get_file_contents.assert_has_calls(
            redis_repo_get_file_calls)
        wordpress_repo.get_file_contents.assert_has_calls(
            wordpress_repo_get_file_calls)
        decode_calls = [
            mock.call('redis_template'),
            mock.call('redis_metadata'),
            mock.call('wordpress_template')
        ]
        mock_decode.assert_has_calls(decode_calls)

    @mock.patch('base64.b64decode')
    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_get_template_with_metadata(self, mock_get_client, mock_decode):
        redis_template = """
        description: |
            Simple template to deploy Redis on a cloud server
        version: stable
        id: '1234'
        """
        redis_metadata = """
        meta: |
            Metadata for redis template
        """
        mock_client = mock_get_client.return_value
        mock_org = mock_client.get_organization.return_value
        mock_repo = mock.MagicMock(id=1234)
        mock_org.get_repos.return_value = [mock_repo]
        mock_repo.get_file_contents.side_effect = [
            mock.Mock(content="template"), mock.Mock(content="metadata")]
        mock_decode.side_effect = [redis_template, redis_metadata]
        mock_options = mock.Mock(
            github=mock.Mock(api_base="https://api.github.com",
                             organization="heat-templates",
                             metadata_file="heat.metadata",
                             template_file="heat.template"))
        redis_template = yaml.load(redis_template)
        redis_template.update(yaml.load(redis_metadata))

        manager = managers.GithubManager(mock_options)
        template = manager.get_template("1234", "stable", True)

        self.assertEqual(template, redis_template)
        get_calls = [
            mock.call("heat.template", ref="stable"),
            mock.call("heat.metadata", ref="stable"),
        ]
        decode_calls = [
            mock.call("template"),
            mock.call("metadata"),
        ]
        self.assertTrue(mock_get_client.called)
        mock_repo.get_file_contents.assert_has_calls(get_calls)
        mock_decode.assert_has_calls(decode_calls)
        mock_client.get_organization.assert_called_once_with("heat-templates")
        self.assertTrue(mock_org.get_repos.called)

    @mock.patch('base64.b64decode')
    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_get_template_without_metadata(self, mock_get_client, mock_decode):
        redis_template = """
        description: |
            Simple template to deploy Redis on a cloud server
        version: stable
        id: '1234'
        """
        mock_client = mock_get_client.return_value
        mock_repo = mock.MagicMock(id=1234)
        mock_org = mock_client.get_organization.return_value
        mock_org.get_repos.return_value = [mock_repo]
        mock_repo.get_file_contents.side_effect = [
            mock.Mock(content="template"), mock.Mock(content="metadata")]
        mock_decode.return_value = redis_template
        mock_options = mock.Mock(
            github=mock.Mock(api_base="https://api.github.com",
                             organization="heat-templates",
                             metadata_file="heat.metadata",
                             template_file="heat.template"))
        redis_template = yaml.load(redis_template)

        manager = managers.GithubManager(mock_options)
        template = manager.get_template(1234, "stable", False)

        self.assertEqual(template, redis_template)
        self.assertTrue(mock_get_client.called)
        mock_repo.get_file_contents.assert_called_once_with("heat.template",
                                                            ref="stable")
        mock_decode.assert_called_once_with("template")
        mock_client.get_organization.assert_called_once_with("heat-templates")
        self.assertTrue(mock_org.get_repos.called)
