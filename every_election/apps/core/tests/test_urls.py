import json
from django.test import TestCase
from django_extensions.management.commands.show_urls import Command


class UrlTests(TestCase):

    def test_trailing_slashes(self):
        c = Command()
        data = json.loads(
            c.handle(**{
                "unsorted": False,
                "language": None,
                "decorator": [],
                "format_style": "json",
                "urlconf": "ROOT_URLCONF",
            })
        )
        urls = [rec['url'] for rec in data]
        for url in urls:
            assert url[-1] == '/', url + " does not end with /"
