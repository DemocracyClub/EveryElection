import os

from django.conf import settings
from django.http import HttpResponse


def get_election_fixture(request):
    with open(
        os.path.join(settings.BASE_DIR, "data/elections.json")
    ).read() as out:
        return HttpResponse(out, status=200, content_type="application/json")
