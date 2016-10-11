from django.views.generic import ListView

from .models import ElectionType

class ElectionTypesView(ListView):
    template_name = "elections/election_types.html"
    model = ElectionType
