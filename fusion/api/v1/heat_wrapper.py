from paste import proxy as wsgi_proxy
from webob import exc

from fusion.api.templates import template_manager as managers
from fusion.common import wsgi
from fusion.db.sqlalchemy import api as db_api


import logging

logger = logging.getLogger(__name__)


class HeatWrapperController(object):

    def __init__(self, options):
        self._options = options
        heat_host = options.proxy.heat_host
        heat_protocol = options.proxy.heat_protocol
        if heat_host is None:
            raise Exception("heat_host is not configured!")
        self.proxy = wsgi_proxy.make_transparent_proxy(options, heat_host,
                                                       heat_protocol)
        self._manager = managers.GithubManager(options)

    def stack_create(self, req, tenant_id, body):
        if 'template_id' in body:
            template_id = body['template_id']
            template = self._manager.get_template(template_id,
                                                  'master',
                                                  False)
            if template:
                body['template'] = template.values()[0]
                body.pop('template_id', None)
                is_supported_template = True
                req.body = wsgi.JSONResponseSerializer().to_json(body)
            else:
                return exc.HTTPNotFound("Template with id %s not found" %
                                        template_id)
        else:
            template = body["template"]
            is_supported_template = self._is_supported(template)

        response = req.get_response(self.proxy)
        if response.status_code == 201:
            db_api.stack_create({
                'tenant': tenant_id,
                'stack_id': self._get_stack_id(response),
                'supported': is_supported_template
            })
        return response

    def _is_supported(self, template):
        return self._manager.get_catalog().is_supported_template(template)

    def _get_stack_id(self, response):
        body_json = response.json_body
        return body_json["stack"]["id"]


def create_resource(options):
    """
    Templates resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer()
    return wsgi.Resource(HeatWrapperController(options), deserializer,
                         serializer)

