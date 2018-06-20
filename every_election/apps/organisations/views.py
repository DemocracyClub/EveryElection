from django.http import Http404
from django.views.generic import ListView, TemplateView

from .models import Organisation


class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by('organisation_type', 'common_name')


class OrganisationsFilterView(TemplateView):
    template_name = "organisations/organisation_filter.html"
    def get_context_data(self, **kwargs):
        orgs = Organisation.objects.all().filter(**kwargs)
        if not orgs.exists():
            raise Http404()
        return {
            'objects': orgs,
            'context_object_name': 'organisation',
        }


class OrganisationDetailView(TemplateView):
    template_name = "organisations/organisation_detail.html"
    def get_context_data(self, **kwargs):
        try:
            return {
                'object': Organisation.objects.all().get_by_date(**kwargs),
                'context_object_name': 'organisation',
            }
        except Organisation.DoesNotExist:
            raise Http404()
