from django.core.management import BaseCommand

from og_images.svg_maker import SVGGenerator


class Command(BaseCommand):
    def handle(self, *args, **options):
        svg = SVGGenerator(21888)
        svg.write_svg()
