from unittest import TestCase

from core.unified_template.unified_template import UnifiedTemplate, UNIFIED_TEMPLATE_TYPE_NAME


class TestUnifiedTemplate(TestCase):
    def test_ordinar_jinja_backward_compatibility(self):
        template = UnifiedTemplate("abc {{input}}")
        self.assertEqual("abc def", template.render({"input": "def"}))

    def test_type_cast_int(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "int",
            "template": "{{ input ** 2 }}"
        })
        self.assertEqual(49, template.render({"input": 7}))

    def test_type_cast_json(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "json",
            "template": "{{ input }}"
        })
        self.assertEqual([1, 2, 3], template.render({"input": [1, 2, 3]}))

    def test_support_templates(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "support_templates": {
                "name": "{{ personInfo.name|capitalize }}",
                "surname": "{{ personInfo.surname|capitalize }}"
            },
            "template": "{{ name }} {{ surname }}",
        })
        self.assertEqual("Vasya Pupkin", template.render({"personInfo": {"name": "vasya", "surname": "pupkin"}}))

    def test_args_format_input(self):
        template = UnifiedTemplate("timestamp: {{ts}}")
        self.assertEqual("timestamp: 123.45", template.render(ts=123.45))

    def test_bool_cast_false(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "False"
        })
        self.assertFalse(template.render({}))

    def test_bool_cast_false_lowercase(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "false"
        })
        self.assertFalse(template.render({}))

    def test_bool_cast_true(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "True"
        })
        self.assertTrue(template.render({}))

    def test_bool_cast_true_lowercase(self):
        template = UnifiedTemplate({
            "type": UNIFIED_TEMPLATE_TYPE_NAME,
            "loader": "bool",
            "template": "true"
        })
        self.assertTrue(template.render({}))
