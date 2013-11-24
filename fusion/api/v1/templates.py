import base64 as base64

from fusion.common import wsgi
import fusion.api.templates.template_manager as managers


class TemplateController(object):
    """
    WSGI controller for template resource in Heat v1 API
    Implements the API actions
    """

    def __init__(self, options):
        self._options = options
        self._manager = managers.GithubManager(options)

    def get_catalog(self, req):
        """
        Gets template
        """
        catalog = self._manager.get_catalog(as_json=True)
        return catalog


class TemplateSerializer(object):
    pass


def create_resource(options):
    """
    Templates resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = wsgi.JSONResponseSerializer
    return wsgi.Resource(TemplateController(options), deserializer, serializer)

