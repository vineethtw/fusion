from paste import proxy as wsgi_proxy
from webob import Response

from fusion.common import wsgi
from oslo.config import cfg

import logging

logger = logging.getLogger(__name__)


class ProxyMiddleware(wsgi.Middleware):
    def __init__(self, app, conf, **local_conf):
        self.app = app
        self.proxy = wsgi_proxy.make_transparent_proxy(
            conf, cfg.CONF.proxy.heat_endpoint)
        super(ProxyMiddleware, self).__init__(app)

    def process_request(self, req):
        logger.warn("Entering proxy middleware")
        routes_middlware = self.app(req)
        matched = routes_middlware.mapper.routematch(environ=req.environ)
        if not matched:
            return req.get_response(self.proxy)


def ProxyMiddleware_filter_factory(global_conf, **local_conf):
    """
    Factory method for paste.deploy
    """
    conf = global_conf.copy()
    conf.update(local_conf)

    def filter(app):
        return ProxyMiddleware(app, conf)

    return filter
