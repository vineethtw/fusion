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
        req = mock.MagicMock(environ={})
        final_response = mock.MagicMock()
        req.get_response.side_effect = [None, final_response]

        middleware = ProxyMiddleware(app, conf)
        response = middleware.process_request(req)

        self.assertEqual(response, final_response)
        calls = [mock.call(app), mock.call(mock_proxy.return_value)]
        req.get_response.assert_has_calls(calls)

    def test_process_request_by_fusion(self):
        cfg.CONF.reset()
        cfg.CONF = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        app = mock.MagicMock()
        conf = mock.MagicMock()
        req = mock.MagicMock(environ={
            'wsgiorg.routing_args': (None, "200 OK")
        })
        final_response = mock.MagicMock()
        req.get_response.return_value = final_response

        middleware = ProxyMiddleware(app, conf)
        response = middleware.process_request(req)

        self.assertEqual(response, final_response)
        req.get_response.assert_called_once_with(app)
