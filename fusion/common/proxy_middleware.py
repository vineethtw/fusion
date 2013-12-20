from paste import proxy as wsgi_proxy

from fusion.common import wsgi
from oslo.config import cfg

import logging

logger = logging.getLogger(__name__)


class ProxyMiddleware(wsgi.Middleware):
    def __init__(self, app, conf, **local_conf):
        self.app = app
        self.proxy = wsgi_proxy.make_transparent_proxy(
            conf, cfg.CONF.proxy.heat_host)
        super(ProxyMiddleware, self).__init__(app)

    def process_request(self, req):
        routes_middleware = self.app(req)
        matched = routes_middleware.mapper.routematch(environ=req.environ)
        if not matched:
            logger.warn("Proxying call to heat")
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
