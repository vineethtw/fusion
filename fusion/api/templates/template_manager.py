import base64
import github
import json
import yaml

from eventlet import greenpool

from fusion.common import cache, urlfetch
from fusion.common.cache_backing_store import MEMCACHE
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
        self._github_options = options.github
        self._client = self.get_client()

    def __str__(self):
        return "GithubManager: %s, %s, %s" % (
            self._github_options.username,
            self._github_options.template_catalog_path,
            self._github_options.repository_name)

    def __repr__(self):
        return self.__str__()

    def get_client(self):
        return github.Github(self._github_options.username,
                             self._github_options.password,
                             user_agent=self._github_options.username)

    @cache.Cache(store=TEMPLATES, backing_store=MEMCACHE)
    def get_catalog(self):
        repo = self._get_repository()
        file_content = repo.get_file_contents(
            self._github_options.template_catalog_path).content
        decoded_content = base64.b64decode(file_content)
        return decoded_content

    @cache.Cache(store=TEMPLATES, backing_store=MEMCACHE)
    def get_templates(self, with_meta):
        templates = {}
        catalog = self.get_catalog()
        catalog = json.loads(catalog)

        pool = greenpool.GreenPile()
        for template_info in catalog['templates']:
            pool.spawn(self._get_template, template_info, with_meta)
        for result in pool:
            templates.update(result)
        return templates

    @cache.Cache(store=TEMPLATES, backing_store=MEMCACHE)
    def get_template(self, template_id, with_meta):
        catalog = self.get_catalog()
        catalog = json.loads(catalog)
        for template_info in catalog['templates']:
            if template_info.get("id") == template_id:
                return self._get_template(template_info, with_meta)

    def _get_template(self, template_info, with_meta=False):
        template_response = urlfetch.get(template_info.get('url'))
        template = yaml.load(template_response)
        if with_meta and template_info.get('meta_url'):
            metadata_response = urlfetch.get(template_info.get('meta_url'))
            metadata = yaml.load(metadata_response)
            template.update(metadata)
        return {template_info.get('id'): template}

    def _get_user(self):
        return self._client.get_user()

    def _get_repository(self):
        return self._get_user().get_repo(self._github_options.repository_name)
