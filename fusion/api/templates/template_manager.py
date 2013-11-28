import base64
import github
import json
import requests
import yaml

from eventlet import greenpool

from fusion.common.cache import Cache
from fusion.common.cache_backing_store import get_backing_store
from fusion.openstack.common import log as logging

logger = logging.getLogger(__name__)

TEMPLATES = {}


class TemplateManager(object):
    def get_catalog(self):
        logger.warn("TemplateManager.get_catalog called but was not "
                    "implemented")

    def get_templates(self):
        logger.warn("TemplateManager.get_templates called but was not "
                    "implemented")


class GithubManager(TemplateManager):
    def __init__(self, options):
        self._options = options.github
        self._cache_options = options.cache
        self._client = self.get_client()

    def get_client(self):
        return github.Github(self._options.username,
                             self._options.password,
                             user_agent=self._options.username)

    def get_catalog(self):
        repo = self._get_repository()
        file_content = repo.get_file_contents(
            self._options.template_catalog_path).content
        decoded_content = base64.b64decode(file_content)
        return decoded_content

    @Cache(timeout=60, store=TEMPLATES, backing_store=get_backing_store(60))
    def get_templates(self):
        templates = {}
        catalog = self.get_catalog()
        catalog = json.loads(catalog)

        pool = greenpool.GreenPile()
        for template in catalog['templates']:
            pool.spawn(self._get_template, template.get('id'),
                       template.get('url'))

        for result in pool:
            templates.update(result)

        return templates

    def _get_template(self, template_id, template_url):
        response = requests.get(template_url)
        return {template_id: yaml.load(response.content)}

    def _get_user(self):
        return self._client.get_user()

    def _get_repository(self):
        return self._get_user().get_repo(self._options.repository_name)
