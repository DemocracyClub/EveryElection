from django.core.management import BaseCommand


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--review-title",
            action="store",
            help="Review title to crete",
        )
        group.add_argument(
            "--all",
            action="store",
            help="Run command for all reviews that don't have a divset",
        )
