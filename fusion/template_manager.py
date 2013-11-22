import os
import urlparse
import github
import time


class TemplateManager(object):
    pass


class GitHubManager(TemplateManager):
    def __init__(self, conf):
        git_config = conf.git_config
        self._github_api_base = git_config.github_api
        if self._github_api_base:
            self._github = github.Github(base_url=self._github_api_base)
            self._api_host = urlparse.urlparse(self._github_api_base).netloc
        self._repo_org = git_config.organization
        self._ref = git_config.ref
        self._cache_root = git_config.cache_dir or os.path.dirname(__file__)
        self._cache_file = os.path.join(self._cache_root, ".blueprint_cache")
        self._blueprints = {}
        self._preview_ref = git_config.preview_ref
        self._preview_tenants = git_config.preview_tenants
        self._group_refs = git_config.group_refs or {}
        self._groups = set(self._group_refs.keys())
        assert self._github_api_base, ("Must specify a source blueprint "
                                       "repository")
        assert self._repo_org, ("Must specify a Github organization owning "
                                "blueprint repositories")
        assert self._ref, "Must specify a branch or tag"
        self.background = None