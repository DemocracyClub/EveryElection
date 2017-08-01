from io import StringIO
from django.core.management import call_command
from django.http import HttpResponse


def get_election_fixture(request):

    out = StringIO()
    call_command('dumpdata', 'elections', stdout=out)

    return HttpResponse(out.getvalue(),
        status=200, content_type='application/json')
