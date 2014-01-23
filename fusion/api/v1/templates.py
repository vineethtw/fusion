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
Templates endpoint for fusion v1 ReST API.
"""

from webob import exc

from fusion.api.templates import template_manager as managers
from fusion.common import wsgi
from fusion.openstack.common import log as logging

logger = logging.getLogger(__name__)


class TemplateController(object):
    """
    WSGI controller for template resource in Heat v1 API
    Implements the API actions
    """

    def __init__(self, options):
        self._options = options
        self._manager = managers.GithubManager(options)

    def get_templates(self, req):
        """
        Gets all templates
        """
        with_meta = True if 'with_meta' in req.params else False
        default_version = self._options.github.default_version
        return {"templates": self._manager.get_templates([default_version],
                                                 with_meta)}

    def get_template(self, req, template_id):
        """
        Get template
        """
        default_version = self._options.github.default_version
        with_meta = True if 'with_meta' in req.params else False
        version = (req.params['version'] if 'version' in req.params
                   else default_version)

        template = self._manager.get_template(template_id, version,
                                              with_meta)
        if not template:
            return exc.HTTPNotFound()
        return {"template": template}


def create_resource(options):
    """
    Templates resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(TemplateController(options), deserializer, serializer)
