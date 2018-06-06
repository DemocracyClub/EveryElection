from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import ListView, TemplateView, View

from .models import Organisation


class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by('organisation_type', 'common_name')


class OrganisationsFilterView(TemplateView):
    template_name = "organisations/organisation_filter.html"
    def get_context_data(self, **kwargs):
        return {
            'objects': Organisation.objects.all().filter(**kwargs),
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


class OrganisationCompatibilityView(View):

    def get(self, request, *args, **kwargs):

        org = Organisation.objects.all().get(**kwargs)
        # if get() returns more than one Organisation
        # don't attempt to handle it, just throw a 500

        return HttpResponseRedirect(
            reverse('organisation_view', args=(
                    org.organisation_type,
                    org.official_identifier,
                    org.start_date
                )
            )
        )
