import logging

from paste import proxy as wsgi_proxy

from fusion.common import wsgi
from oslo.config import cfg

logger = logging.getLogger(__name__)


class ProxyMiddleware(wsgi.Middleware):

    def __init__(self, app, conf, **local_conf):
        self.app = app
        heat_host = cfg.CONF.proxy.heat_host
        heat_protocol = cfg.CONF.proxy.heat_protocol
        if heat_host is None:
            raise Exception("heat_host is not configured!")
        self.proxy = wsgi_proxy.make_transparent_proxy(conf, heat_host,
                                                       heat_protocol)
        super(ProxyMiddleware, self).__init__(app)

    def process_request(self, request):
        response = request.get_response(self.app)
        match = request.environ.get('wsgiorg.routing_args', (None, None))[1]
        if not match:
            logger.debug("Proxying call to heat")
            response = request.get_response(self.proxy)
        return response


def ProxyMiddleware_filter_factory(global_conf, **local_conf):
    """
    Factory method for paste.deploy
    """
    conf = global_conf.copy()
    conf.update(local_conf)

    def filter(app):
        return ProxyMiddleware(app, conf)

    return filter
