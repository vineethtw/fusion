import routes

from fusion.api.v1 import templates
from fusion.api.v1 import heat_wrapper
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
            template_mapper.connect("get_templates",
                                    "/templates",
                                    action="get_templates",
                                    conditions={'method': 'GET'})
            template_mapper.connect("get_template",
                                    "/templates/{template_id}",
                                    action="get_template",
                                    conditions={'method': 'GET'})

        heat_wrapper_resource = heat_wrapper.create_resource(conf)
        with mapper.submapper(
                controller=heat_wrapper_resource,
                path_prefix="/{tenant_id}") as heat_wrapper_mapper:
            heat_wrapper_mapper.connect("stack_create",
                                        "/stacks",
                                        action="stack_create",
                                        conditions={'method': 'POST'})


