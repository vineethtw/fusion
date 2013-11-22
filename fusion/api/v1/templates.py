from fusion.common import wsgi


class TemplateController(object):
    """
    WSGI controller for template resource in Heat v1 API
    Implements the API actions
    """

    def __init__(self, options):
        self.options = options

    def show(self, req, template_id):
        """
        Gets template
        """
        return "foo"


class TemplateSerializer(object):
    pass


def create_resource(options):
    """
    Templates resource factory method.
    """
    deserializer = wsgi.JSONRequestDeserializer()
    serializer = TemplateSerializer()
    return wsgi.Resource(TemplateController(options), deserializer, serializer)