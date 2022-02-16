from datetime import datetime
from django.db.models import Prefetch, Q
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, TemplateView
from organisations.models import Organisation
from elections.models import Election


class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by("organisation_type", "common_name")


class OrganisationsFilterView(TemplateView):
    template_name = "organisations/organisation_filter.html"

    def get_context_data(self, **kwargs):
        orgs = Organisation.objects.all().filter(**kwargs)
        if not orgs.exists():
            raise Http404()

        paginator = Paginator(orgs, 100)  # Show 100 records per page
        page = self.request.GET.get("page")
        context = {"context_object_name": "organisation"}
        try:
            context["objects"] = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            context["objects"] = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            context["objects"] = paginator.page(paginator.num_pages)

        return context


class OrganisationDetailView(TemplateView):
    template_name = "organisations/organisation_detail.html"

    def get_context_data(self, **kwargs):
        kwargs["date"] = datetime.strptime(kwargs["date"], "%Y-%m-%d").date()

        mayor_q = Q(election_id__startswith="mayor")
        pcc_q = Q(election_id__startswith="pcc")
        ref_q = Q(election_id__startswith="ref")
        others_q = Q(group_type__isnull=False) & ~Q(group_type="subtype")
        elections = Election.public_objects.filter(others_q | pcc_q | mayor_q | ref_q)

        try:
            obj = (
                Organisation.objects.all()
                .prefetch_related(Prefetch("election_set", elections))
                .get_by_date(**kwargs)
            )
        except Organisation.DoesNotExist:
            raise Http404()

        context = {
            "object": obj,
            "api_detail": obj.get_url("api:organisation-detail"),
            "context_object_name": "organisation",
        }
        if obj.get_geography(kwargs["date"]):
            context["api_detail_geo"] = obj.get_url("api:organisation-geo", "json")
        return context
