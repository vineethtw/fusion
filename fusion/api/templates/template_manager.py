import base64
import github
import json
import requests
import yaml


class TemplateManager(object):
    pass


class GithubManager(TemplateManager):

    def __init__(self, options):
        self._options = options.github
        self._client = self.get_client()

    def get_client(self):
        return github.Github(self._options.username,
                             self._options.password)

    def get_catalog(self):
        repo = self._get_repository()
        file_content = repo.get_file_contents(
            self._options.template_catalog_path).content
        decoded_content = base64.b64decode(file_content)
        return decoded_content

    def get_templates(self):
        templates = {}
        catalog = self.get_catalog()
        catalog = json.loads(catalog)

        for template in catalog['templates']:
            response = requests.get(template.get('url'))
            templates[template.get('id')] = yaml.load(response.content)
        return templates

    def _get_user(self):
        return self._client.get_user()

    def _get_repository(self):
        return self._get_user().get_repo(self._options.repository_name)
