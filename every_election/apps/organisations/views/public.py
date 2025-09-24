from datetime import datetime

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Prefetch, Q
from django.http import FileResponse, Http404
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, View
from elections.models import Election
from organisations.models import (
    Organisation,
    OrganisationBoundaryReview,
    OrganisationDivisionSet,
)


class SupportedOrganisationsView(ListView):
    template_name = "organisations/supported_organisations.html"
    queryset = Organisation.objects.all().order_by(
        "organisation_type", "common_name"
    )


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
        elections = Election.public_objects.filter(
            others_q | pcc_q | mayor_q | ref_q
        )

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
            context["api_detail_geo"] = obj.get_url(
                "api:organisation-geo", "json"
            )
        return context


class AllBoundaryReviewsView(ListView):
    template_name = "organisations/organisationboundaryreviews_list.html"
    model = OrganisationBoundaryReview
    context_object_name = "boundary_reviews"

    def get_context_data(self, **kwargs):
        from ..filters import OrganisationBoundaryReviewFilter

        context = super().get_context_data(**kwargs)
        qs = (
            OrganisationBoundaryReview.objects.all()
            .prefetch_related("organisation")
            .prefetch_related("divisionset")
            .order_by("organisation")
        )
        f = OrganisationBoundaryReviewFilter(self.request.GET, qs)

        context["filter"] = f
        context["queryset"] = f.qs
        return context


class SingleBoundaryReviewView(DetailView):
    model = OrganisationBoundaryReview
    context_object_name = "boundary_review"
    slug_field = "id"
    slug_url_kwarg = "boundary_review_id"


class DivisionsetDetailView(DetailView):
    template_name = "organisations/divisionset_detail.html"

    model = OrganisationDivisionSet
    context_object_name = "divisionset"
    slug_field = "id"
    slug_url_kwarg = "divisionset_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.has_pmtiles_file:
            if settings.PUBLIC_DATA_BUCKET:
                context["pmtiles_source_link"] = (
                    f"https://s3.eu-west-2.amazonaws.com/{settings.PUBLIC_DATA_BUCKET}/{self.object.pmtiles_s3_key}"
                )
            else:
                context["pmtiles_source_link"] = reverse(
                    "pmtiles_view", args=[self.object.id]
                )

        div_type_and_subtype_pairs = set(
            self.object.divisions.values_list(
                "division_type", "division_subtype"
            )
        )
        # Determine display names for map layer toggle menu
        map_layer_display_name_mapping = {}

        for div_type, div_subtype in div_type_and_subtype_pairs:
            if "region" in div_subtype.lower():
                display_name = "Regions"
            elif "constituency" in div_subtype.lower():
                display_name = "Constituencies"
            else:
                display_name = div_type

            map_layer_display_name_mapping[div_type] = display_name

        context["map_layer_display_name_mapping"] = (
            map_layer_display_name_mapping
        )
        return context


class PMtilesView(View):
    """
    View for serving DivisionSet pmtiles files.
    """

    def get(self, request, divisionset_id):
        try:
            divset = OrganisationDivisionSet.objects.get(id=divisionset_id)
        except OrganisationDivisionSet.DoesNotExist:
            raise Http404("DivisionSet not found")

        if not divset.has_pmtiles_file:
            raise Http404("pmtiles file not found")

        pmtiles_fp = (
            f"{settings.STATIC_ROOT}/pmtiles-store/{divset.pmtiles_file_name}"
        )
        return FileResponse(open(pmtiles_fp, "rb"))  # noqa SIM115
