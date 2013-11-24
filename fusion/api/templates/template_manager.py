import os
import urlparse
import github
import time
import base64

from fusion.api.templates import TemplateCatalog

class TemplateManager(object):
    pass

class GithubManager(TemplateManager):

    def __init__(self, options):
        self._options = options.github
        self._client = self.get_client()

    def get_client(self):
        return github.Github(self._options.username,
                             self._options.password)

    def __get_user(self):
        return self._client.get_user()

    def __get_repository(self):
        return self.__get_user().get_repo(self._options.repository_name)

    def get_catalog(self, as_json=False):
        repo = self.__get_repository()
        file_content = repo.get_file_contents(
            self._options.template_catalog_path).content
        decoded_content = base64.b64decode(file_content)

        if as_json:
            return decoded_content
        else:
            return TemplateCatalog.from_json(decoded_content)







