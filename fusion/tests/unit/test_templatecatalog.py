import unittest
import yaml

from fusion.api.templates.template_manager import TemplateCatalog

class TemplateCatalogTest(unittest.TestCase):

    def test_should_say_if_supported_template(self):
        template1 = """
            description: Template on the catalog
            parameters:
                flavor:
                    description: Rackspace Cloud Server Flavor
                    type: String
                image:
                    type: String

            resources:
                repose_server:
                    type: \"Rackspace:Cloud:Server\"

        """

        template2 = """
            description: Template on the catalog
            parameters:
                flavor:
                    description: Rackspace Cloud Server Flavor
                    type: String
                image:
                    type: String

            resources:
                repose_server:
                    type: \"Rackspace:Cloud:Server\"

        """

        catalog = TemplateCatalog({
            "template1": yaml.load(template1)
        })

        supported = catalog.is_supported_template(template2)
        self.assertTrue(supported)


    def test_should_say_if_supported_template(self):
        template1 = """
            description: Template on the catalog
            parameters:
                flavor:
                    description: Rackspace Cloud Server Flavor
                    type: String
                image:
                    type: String

            resources:
                repose_server:
                    type: \"Rackspace:Cloud:Server\"

        """

        template2 = """
            description: Template on the catalog
            parameters:
                flavor:
                    description: Rackspace Cloud Server Flavor
                    type: String
                image:
                    type: String

            resources:
                repose_server:
                    type: \"Rackspace:Cloud:Server\"

                another_repose_server:
                    type: \"Rackspace:Cloud:Server\"

        """

        catalog = TemplateCatalog({
            "template1": yaml.load(template1)
        })

        supported = catalog.is_supported_template(template2)
        self.assertFalse(supported)

