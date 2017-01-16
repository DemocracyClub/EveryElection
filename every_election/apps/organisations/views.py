from django.views.generic import ListView, DetailView

from .models import Organisation

class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by('organisation_type', 'common_name')

class OrganisationsView(DetailView):
    queryset = Organisation.objects.all()
    slug_url_kwarg = 'official_identifier'
    slug_field = 'official_identifier'
