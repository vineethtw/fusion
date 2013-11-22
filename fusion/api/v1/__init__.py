import routes

from fusion.api.v1 import templates
from fusion.common import wsgi


class API(wsgi.Router):
    def __init__(self, conf, **local_conf):
        self.conf = conf
        mapper = routes.Mapper()
        templates_resource = templates.create_resource(conf)
        super(API, self).__init__(mapper)

        with mapper.submapper(controller=templates_resource) as \
                template_mapper:
            # Template handling
            template_mapper.connect("template_show",
                                    "/templates/{template_id}",
                                    action="show",
                                    conditions={'method': 'GET'})
