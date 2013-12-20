import mock
import unittest

from paste import proxy as wsgi_proxy
from oslo.config import cfg

from fusion.common.proxy_middleware import ProxyMiddleware


class ProxyMiddlewareTest(unittest.TestCase):
    @mock.patch.object(wsgi_proxy, 'make_transparent_proxy')
    def test_process_request_proxies_to_heat(self, mock_proxy):
        cfg.CONF.reset()
        cfg.CONF = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        app = mock.MagicMock()
        conf = mock.MagicMock()
        req = mock.MagicMock()
        req.get_response.return_value = "200 OK"
        routes_middleware = app.return_value
        routes_middleware.mapper.routematch.return_value = None

        middleware = ProxyMiddleware(app, conf)
        response = middleware.process_request(req)
        self.assertEqual(response, "200 OK")

        mock_proxy.assert_called_once_with(conf, "foo.com")
        app.assert_called_once_with(req)
        req.get_response.assert_called_once_with(mock_proxy.return_value)

    @mock.patch.object(wsgi_proxy, 'make_transparent_proxy')
    def test_process_request_by_fusion(self, mock_proxy):
        cfg.CONF.reset()
        cfg.CONF = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        app = mock.MagicMock()
        conf = mock.MagicMock()
        req = mock.MagicMock()
        routes_middleware = app.return_value
        routes_middleware.mapper.routematch.return_value = ("foo", "bar")
        middleware = ProxyMiddleware(app, conf)
        self.assertIsNone(middleware.process_request(req))

        app.assert_called_once_with(req)
        self.assertFalse(req.get_response.called)
        mock_proxy.assert_called_once_with(conf, "foo.com")
