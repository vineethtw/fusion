import base64
import yaml

from eventlet import greenpool
import github
from github import GithubException

from fusion.common import cache
from fusion.common.cache_backing_store import MEMCACHE
from fusion.openstack.common import log as logging

logger = logging.getLogger(__name__)

TEMPLATES = {}


class TemplateManager(object):
    def get_template(self):
        logger.warn("TemplateManager.get_template called but was not "
                    "implemented")

    def get_templates(self):
        logger.warn("TemplateManager.get_templates called but was not "
                    "implemented")


class TemplateCatalog(object):
    def __init__(self, templates):
        self._templates = templates

    def is_supported_template(self, template):
        for template_id, valid_template in self._templates.iteritems():
            if valid_template == template:
                return True

        return False


class GithubManager(TemplateManager):
    def __init__(self, options):
        self._github_options = options.github
        self._client = self.get_client()
        self._repo_org = self._github_options.organization
        self._metadata_file = self._github_options.metadata_file
        self._template_file = self._github_options.template_file

    def get_client(self):
        return github.Github(login_or_token=self._github_options.username,
                             password=self._github_options.password,
                             base_url=self._github_options.api_base,
                             user_agent="fusion")

    def __str__(self):
        return "GithubManager: %s" % self._repo_org

    def __repr__(self):
        return self.__str__()

    def get_catalog(self):
        tag = self._github_options.default_tag
        return TemplateCatalog(self.get_templates([tag], False))

    @cache.Cache(store=TEMPLATES, backing_store=MEMCACHE)
    def get_templates(self, refs, with_meta):
        """
        Gets all templates owned by self._repo_org organization
        :param refs: refs to fetch
        :param with_meta: include meta info or not
        :return:
        """
        templates = {}
        org = self._get_repo_owner()
        repos = org.get_repos()
        pool = greenpool.GreenPile()
        for ref in refs:
            for repo in repos:
                pool.spawn(self._get_template, repo, ref, with_meta)
        for result in pool:
            if result:
                templates.update(result)
        return templates

    @cache.Cache(store=TEMPLATES, backing_store=MEMCACHE)
    def get_template(self, template_id, ref, with_meta):
        try:
            org = self._get_repo_owner()
            repos = org.get_repos()
            template_repo = None
            for repo in repos:
                if str(repo.id) == str(template_id):
                    template_repo = repo
                    break
            if template_repo:
                return self._get_template(template_repo, ref, with_meta)
        except GithubException:
            logger.error("Unexpected error getting template from repo %s",
                         repo.clone_url, exc_info=True)

    def _get_template(self, repo, ref, with_meta):
        try:
            template = self._get_file_from_repo(repo, ref, self._template_file)
            if template:
                template.update({
                    'id': str(repo.id),
                    'version': ref
                })
                if with_meta:
                    metadata = self._get_file_from_repo(repo, ref,
                                                        self._metadata_file)
                    template.update(metadata)
                return {str(repo.id): template}
        except GithubException:
            logger.error("Unexpected error getting template from repo %s",
                         repo.clone_url, exc_info=True)
        return None

    @staticmethod
    def _get_file_from_repo(repo, ref, file_name):
        try:
            encoded_file = repo.get_file_contents(file_name, ref=ref)
            if encoded_file and encoded_file.content:
                file_content = base64.b64decode(encoded_file.content)
                return yaml.load(file_content)
        except (yaml.scanner.ScannerError, yaml.parser.ParserError):
            logger.warn("Template '%s' has invalid YAML", repo.clone_url)
        return {}

    def _get_repo_owner(self):
        """Return the user or organization owning the repo."""
        if self._repo_org:
            try:
                return self._client.get_organization(self._repo_org)
            except GithubException:
                logger.debug("Could not retrieve org information for %s; "
                             "trying users", self._repo_org, exc_info=True)
                try:
                    return self._client.get_user(self._repo_org)
                except GithubException:
                    logger.warn("Could not find user or org %s.",
                                self._repo_org)
