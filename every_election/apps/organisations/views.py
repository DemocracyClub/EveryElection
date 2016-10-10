from django.views.generic import ListView

from .models import Organisation

class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    model = Organisation
