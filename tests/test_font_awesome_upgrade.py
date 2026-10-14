import json
from pathlib import Path

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase


class FontAwesomeDependencyTests(SimpleTestCase):
    def test_package_json_uses_font_awesome_7_alias(self):
        package_json = json.loads(Path('package.json').read_text())

        self.assertEqual(
            package_json['dependencies']['fontawesome-free'],
            'npm:@fortawesome/fontawesome-free@^7.0.0',
        )

    def test_yarn_lock_resolves_font_awesome_7(self):
        yarn_lock = Path('yarn.lock').read_text()

        self.assertIn('fontawesome-free: "npm:@fortawesome/fontawesome-free@^7.0.0"', yarn_lock)
        self.assertIn('"fontawesome-free@npm:@fortawesome/fontawesome-free@^7.0.0":', yarn_lock)
        self.assertIn('resolution: "@fortawesome/fontawesome-free@npm:7.0.0"', yarn_lock)


class BaseHeadTemplateTests(SimpleTestCase):
    def test_base_head_loads_font_awesome_vendor_stylesheet(self):
        request = RequestFactory().get('/')
        request.user = type('User', (), {'id': None})()

        html = render_to_string('helpdesk/base-head.html', {'request': request, 'user': request.user})

        self.assertIn('rel="stylesheet"', html)
        self.assertIn('helpdesk/vendor/fontawesome-free/css/all.min.css', html)
