import sys
from django.core.management.base import BaseCommand
from elections.constraints import check_constraints, ViolatedConstraint
from elections.models import Election


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        elections = Election.private_objects.all()
        exitcode = 0
        for election in elections:
            try:
                check_constraints(election)
            except ViolatedConstraint as e:
                exitcode = 1
                self.stderr.write(str(e))
        sys.exit(exitcode)
