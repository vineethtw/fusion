
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Routines for configuring Fusion
"""

import logging as sys_logging
import os

from oslo.config import cfg

from fusion.common import wsgi

from fusion.openstack.common import log as logging
import traceback

DEFAULT_PORT = 8000

logger = logging.getLogger(__name__)

paste_deploy_group = cfg.OptGroup('paste_deploy')
paste_deploy_opts = [
    cfg.StrOpt('flavor',
               help=_("The flavor to use")),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               help=_("The API paste config file to use"))]

service_opts = [
    cfg.IntOpt('max_template_size',
               default=524288,
               help='Maximum raw byte size of any template.')
]

github_group = cfg.OptGroup('github')
github_opts = [
    cfg.StrOpt('api_base',
               default="https://api.github.com",
               help="Github API base path"),
    cfg.StrOpt('organization',
               default="",
               help="organization owning all the templates"),
    cfg.StrOpt('template_file',
               default="",
               help="name of the template file"),
    cfg.StrOpt('metadata_file',
               default="",
               help="name of the metadata file"),
    cfg.StrOpt('username',
               default="",
               help="github username"),
    cfg.StrOpt('password',
               default="",
               help="github password")
]

cache_group = cfg.OptGroup('cache')
cache_opts = [
    cfg.StrOpt('cache_root',
               default="cache_root was not defined!",
               help="Location for cache folder"),
    cfg.IntOpt('default_timeout',
               default=3600,
               help="default timeout for filesystem cache"),
    cfg.StrOpt('redis_connection_string',
               default="redis_connection_string was not defined!",
               help="redis connection string"),
    cfg.ListOpt('memcache_servers',
                default="memcache_servers was not defined!",
                help="memcache servers"),
]

proxy_group = cfg.OptGroup('proxy')
proxy_opts = [
    cfg.StrOpt('heat_host',
               default=None,
               help="Heat host")
]

cfg.CONF.register_opts(service_opts)
cfg.CONF.register_group(paste_deploy_group)
cfg.CONF.register_opts(paste_deploy_opts, group=paste_deploy_group)
cfg.CONF.register_opts(github_opts, group=github_group)
cfg.CONF.register_opts(cache_opts, group=cache_group)
cfg.CONF.register_opts(proxy_opts, group=proxy_group)


def _get_deployment_flavor():
    """
    Retrieve the paste_deploy.flavor config item, formatted appropriately
    for appending to the application name.
    """
    flavor = cfg.CONF.paste_deploy.flavor
    return '' if not flavor else ('-' + flavor)


def _get_deployment_config_file():
    """
    Retrieve the deployment_config_file config item, formatted as an
    absolute pathname.
    """
    config_path = cfg.CONF.find_file(
        cfg.CONF.paste_deploy['api_paste_config'])
    if config_path is None:
        return None

    return os.path.abspath(config_path)


def load_paste_app(app_name=None):
    """
    Builds and returns a WSGI app from a paste config file.

    We assume the last config file specified in the supplied ConfigOpts
    object is the paste config file.

    :param app_name: name of the application to load

    :raises RuntimeError when config file cannot be located or application
            cannot be loaded from config file
    """
    if app_name is None:
        app_name = cfg.CONF.prog

    # append the deployment flavor to the application name,
    # in order to identify the appropriate paste pipeline
    app_name += _get_deployment_flavor()

    conf_file = _get_deployment_config_file()
    if conf_file is None:
        raise RuntimeError(_("Unable to locate config file"))

    try:
        app = wsgi.paste_deploy_app(conf_file, app_name, cfg.CONF)

        # Log the options used when starting if we're in debug mode...
        if cfg.CONF.debug:
            cfg.CONF.log_opt_values(logging.getLogger(app_name),
                                    sys_logging.DEBUG)

        return app
    except (LookupError, ImportError) as e:
        traceback.format_exc()
        raise RuntimeError(_("Unable to load %(app_name)s from "
                             "configuration file %(conf_file)s."
                             "\nGot: %(e)r") % {'app_name': app_name,
                                                'conf_file': conf_file,
                                                'e': e})

def safe_get_config(group, name):
    if group not in cfg.CONF:
        logger.warn("Could not find %s group in the configuration file! This"
                    "might be cause due to bad configuration.")
        return None
    return getattr(getattr(cfg.CONF, group),name)
