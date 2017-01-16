from django.views.generic import ListView, DetailView

from elections.models import ElectionType, Election


class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType


class AllElectionsView(ListView):
    template_name = "elections/elections.html"
    model = Election
    paginate_by = 50


class SingleElection(DetailView):
    model = Election
    slug_url_kwarg = 'election_id'
    slug_field = 'election_id'
