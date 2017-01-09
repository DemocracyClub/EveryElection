from django.views.generic import ListView

from elections.models import ElectionType, Election


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


class AllElectionsView(ListView):
    template_name = "elections/elections.html"
    model = Election
    paginate_by = 50
