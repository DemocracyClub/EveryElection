from django.views.generic import ListView

from .models import Organisation

class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by('organisation_type', 'common_name')
