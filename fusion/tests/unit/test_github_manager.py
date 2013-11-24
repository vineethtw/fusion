import unittest
import mock
import github
from fusion.api.templates import template_manager as managers


class TemplateTests(unittest.TestCase):

    @mock.patch(managers.GithubManager, 'get_client')
    def test_should_get_catalog_as_json(self, get_client):
        client = mock.MagicMock()
        options = mock.MagicMock(
            github = mock.MagicMock(template_catalog_path="catalog_path",
                                    repository_name="repo"))

        mock_repo = mock.MagicMock()
        mock_repo.get_file_contents.return_value = mock.MagicMock(
            content = "YmFzZV82NF9zdHJpbmc==")

        mock_user = mock.MagicMock()
        mock_user.get_repo.return_value = mock_repo
        client.get_user.return_value = mock_user
        get_client.return_value = client

        manager = managers.GithubManager(options)
        catalog = manager.get_catalog(as_json=True)

        self.assertEquals("base_64_string", catalog)

        mock_repo.get_file_contents.assert_called_once_with("catalog_path")
        mock_user.get_repo.assert_called_once_with("repo")

    @mock.patch.object(managers.GithubManager, 'get_client')
    def test_should_get_catalog(self, get_client):
        client = mock.MagicMock()
        options = mock.MagicMock(
            github = mock.MagicMock(template_catalog_path="catalog_path",
                                    repository_name="repo"))

        mock_repo = mock.MagicMock()
        mock_repo.get_file_contents.return_value = mock.MagicMock(
            content = "eyJ0ZW1wbGF0ZXMiOiBbIHsgImlk"
                      "IjogMSwibmFtZSI6Im5hbWUifV19")

        mock_user = mock.MagicMock()
        mock_user.get_repo.return_value = mock_repo
        client.get_user.return_value = mock_user
        get_client.return_value = client

        manager = managers.GithubManager(options)
        catalog = manager.get_catalog()

        self.assertEquals(1, catalog.size())
        self.assertEquals(1, catalog[0].id)
        self.assertEquals('name', catalog[0].name)

        mock_repo.get_file_contents.assert_called_once_with("catalog_path")
        mock_user.get_repo.assert_called_once_with("repo")