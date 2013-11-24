import unittest
from fusion.api.templates import TemplateCatalogEntry, TemplateCatalog

class TemplateTests(unittest.TestCase):

    def test_can_parse_template_definition(self):
        catalog = TemplateCatalog([{"id" : 1, "name": "wordpress"}])
        self.assertEquals(catalog.size(), 1)
        self.assertEquals(catalog[0].name, "wordpress")

    def test_can_create_a_catalog_from_list_of_templates(self):
        template1 = TemplateCatalogEntry({"name": "wordpress"})
        template2 = TemplateCatalogEntry({"name": "php"})
        catalog = TemplateCatalog([template1, template2])

        self.assertEquals(catalog.size(), 2)
        self.assertEquals(catalog[0].name, "wordpress")
        self.assertEquals(catalog[1].name, "php")

    def test_should_raise_exception_invalid_input_to_catalog(self):
        template = TemplateCatalogEntry({"name": "wordpress"})
        self.assertRaises(TypeError, TemplateCatalog, [
            template, "this_will_cause_an_exception"])




