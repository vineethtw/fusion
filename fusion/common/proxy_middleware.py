from paste import proxy as wsgi_proxy
from fusion.api.templates import template_manager as managers

from fusion.db.sqlalchemy import api as db_api


from fusion.common import wsgi
from oslo.config import cfg

import json
import datetime

import logging

logger = logging.getLogger(__name__)


class ProxyMiddleware(wsgi.Middleware):

    def __init__(self, app, conf, **local_conf):
        self.app = app
        heat_host = cfg.CONF.proxy.heat_host
        if heat_host is None:
            raise Exception("heat_host is not configured!")
        self.proxy = wsgi_proxy.make_transparent_proxy(conf, heat_host)
        super(ProxyMiddleware, self).__init__(app)
        self._manager = managers.GithubManager(cfg.CONF)

    def process_request(self, request):
        environment = request.environ
        (tenant_id, action) = environment['PATH_INFO'][1:].split('/')
        is_supported_template = False

        if (action == 'stack_create'):
            if 'template_id' in request_body:
                self._substitute_template_ids_with_templates(request)
                is_supported_template = True
            else:
                template = request.json_body["template"]
                is_supported_template = self._is_supported(template)

        if not self._can_handle_request(request):
            logger.warn("Proxying call to heat")
            logger.warn("with body: %s", request.body)
            response = request.get_response(self.proxy)
            if (action == 'stack_create'):
                db_api.stack_create({'tenant': tenant_id,
                                     'stack_id': self._get_stack_id(response),
                                     'supported': is_supported_template}
                )
            return response

    def _get_stack_id(self, response):
        return "stack_id"

    def _substitute_template_ids_with_templates(self, request):
        def sanitizer(obj):
            if (isinstance(obj, datetime.datetime) or isinstance(
                    obj, datetime.date)):
                return obj.isoformat()
            return obj

        request_body = request.json_body
        template_id = request_body['template_id']
        template = self._manager.get_template(template_id, 'master', False)
        if template:
            request_body['template'] = template.values()[0] 
            request_body.pop('template_id', None)
        request.body = json.dumps(request_body, default=sanitizer)
        logger.warn("[RequestBody] %s", request.body)

    def _is_supported(self, template):
        logger.warn("[Custom Template] %s", template)
        return self._manager.get_catalog().is_supported_template(template)

    def _can_handle_request(self, request):
        routes_middleware = self.app(request)
        matched = routes_middleware.mapper.routematch(environ=request.environ)
        return matched


def ProxyMiddleware_filter_factory(global_conf, **local_conf):
    """
    Factory method for paste.deploy
    """
    conf = global_conf.copy()
    conf.update(local_conf)

    def filter(app):
        return ProxyMiddleware(app, conf)

    return filter
