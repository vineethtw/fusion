import mock
import unittest

from paste import proxy as wsgi_proxy
from oslo.config import cfg
from webob import exc

from fusion.api.templates import template_manager as managers
from fusion.api.v1.heat_wrapper import HeatWrapperController
from fusion.common.proxy_middleware import ProxyMiddleware
from fusion.db.sqlalchemy import api

class HeatWrapperControllerTest(unittest.TestCase):

    @mock.patch.object(wsgi_proxy, 'make_transparent_proxy')
    @mock.patch.object(managers, 'GithubManager')
    @mock.patch.object(api, 'stack_create' )
    def test_stack_create_with_template(self, stack_create, manager, proxy):
        options = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        controller = HeatWrapperController(options)
        request = mock.MagicMock()
        mock_catalog = manager.return_value.get_catalog.return_value
        mock_catalog.is_supported_template.return_value = True
        controller.stack_create(request, '10021', {'template':{}})
        request.get_response.assert_called_once_with(proxy.return_value)
        stack_create.assert_called_once_with({
            'tenant': '10021',
            'stack_id': "stack_id",
            'supported': True
        })

    @mock.patch.object(wsgi_proxy, 'make_transparent_proxy')
    @mock.patch.object(managers, 'GithubManager')
    @mock.patch.object(api, 'stack_create' )
    def test_stack_create_with_template_id(self, stack_create, manager,
                                           proxy):
        options = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        controller = HeatWrapperController(options)
        request = mock.MagicMock()
        manager.return_value.get_template.return_value = {
            "template_id": {
                "key": "value"
            }
        }
        body = {'template_id': 'wordpress'}
        controller.stack_create(request, '10021', body)
        self.assertEquals(request.body, '{"template": {"key": "value"}}')
        request.get_response.assert_called_once_with(proxy.return_value)

        stack_create.assert_called_once_with({
            'tenant': '10021',
            'stack_id': "stack_id",
            'supported': True
        })

    @mock.patch.object(wsgi_proxy, 'make_transparent_proxy')
    @mock.patch.object(managers, 'GithubManager')
    @mock.patch.object(api, 'stack_create' )
    def test_stack_create_with_invalid_template_id(self, stack_create,
                                                   manager, proxy):
        options = mock.Mock(proxy=mock.Mock(heat_host="foo.com"))
        controller = HeatWrapperController(options)
        request = mock.MagicMock()
        manager.return_value.get_template.return_value = None
        body = {'template_id': 'wordpress'}
        result = controller.stack_create(request, '10021', body)

        self.assertIsInstance(result, exc.HTTPNotFound)
        self.assertFalse(request.get_response.called)
        self.assertFalse(stack_create.called)
