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
from fusion.common import wsgi, environment_format, template_format
from fusion.common import urlfetch
from fusion.openstack.common import log as logging

logger = logging.getLogger(__name__)


class InstantiationData(object):
    """
    The data accompanying a PUT or POST request to create or update a stack.
    """

    PARAMS = (
        PARAM_STACK_NAME,
        PARAM_TEMPLATE,
        PARAM_TEMPLATE_URL,
        PARAM_USER_PARAMS,
        PARAM_ENVIRONMENT,
        PARAM_FILES,
    ) = (
        'stack_name',
        'template',
        'template_url',
        'parameters',
        'environment',
        'files',
    )

    def __init__(self, data):
        """Initialise from the request object."""
        self.data = data

    @staticmethod
    def format_parse(data, data_type):
        """
        Parse the supplied data as JSON or YAML, raising the appropriate
        exception if it is in the wrong format.
        """
        try:
            if data_type == 'Environment':
                return environment_format.parse(data)
            else:
                return template_format.parse(data)
        except ValueError:
            err_reason = _("%s not in valid format") % data_type
            raise exc.HTTPBadRequest(err_reason)

    def template(self):
        """
        Get template file contents, either inline or from a URL, in JSON
        or YAML format.
        """
        if self.PARAM_TEMPLATE in self.data:
            template_data = self.data[self.PARAM_TEMPLATE]
            if isinstance(template_data, dict):
                return template_data
        elif self.PARAM_TEMPLATE_URL in self.data:
            url = self.data[self.PARAM_TEMPLATE_URL]
            logger.debug('TemplateUrl %s' % url)
            try:
                template_data = urlfetch.get(url)
            except IOError as ex:
                err_reason = _('Could not retrieve template: %s') % str(ex)
                raise exc.HTTPBadRequest(err_reason)
        else:
            raise exc.HTTPBadRequest(_("No template specified"))

        return self.format_parse(template_data, 'Template')

    def environment(self):
        """
        Get the user-supplied environment for the stack in YAML format.
        If the user supplied Parameters then merge these into the
        environment global options.
        """
        env = {}
        if self.PARAM_ENVIRONMENT in self.data:
            env_data = self.data[self.PARAM_ENVIRONMENT]
            if isinstance(env_data, dict):
                env = env_data
            else:
                env = self.format_parse(env_data,
                                        'Environment')

        environment_format.default_for_missing(env)
        parameters = self.data.get(self.PARAM_USER_PARAMS, {})
        env[self.PARAM_USER_PARAMS].update(parameters)
        return env

    def files(self):
        return self.data.get(self.PARAM_FILES, {})

    def args(self):
        """
        Get any additional arguments supplied by the user.
        """
        params = self.data.items()
        return dict((k, v) for k, v in params if k not in self.PARAMS)


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
        return self._manager.get_templates(['stable'], with_meta)

    def get_template(self, req, template_name):
        """
        Get template
        """
        with_meta = True if 'with_meta' in req.params else False
        template = self._manager.get_template(template_name, 'master',
                                              with_meta)
        if not template:
            return exc.HTTPNotFound()
        return template

    def parse_template(self, req, body):
        data = InstantiationData(body)
        env = data.environment()
        template = data.template()
        #Need to find how to get values from parameters and then return it
        # back


def create_resource(options):
    """
    Templates resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(TemplateController(options), deserializer, serializer)

