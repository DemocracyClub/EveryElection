from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.views.generic import FormView
from organisations.boundaries.lgbce_review_helper import LGBCEReviewHelper
from organisations.models import (
    DivisionProblem,
    Organisation,
    OrganisationBoundaryReview,
    OrganisationDivision,
    OrganisationDivisionSet,
    OrganisationGeography,
    OrganisationGeographyProblem,
    OrganisationProblem,
)
from organisations.views.admin.division_problem import DivisionProblemAdmin
from organisations.views.admin.organisation import OrganisationAdmin
from organisations.views.admin.organisation_division import (
    OrganisationDivisionAdmin,
)
from organisations.views.admin.organisation_divisionset import (
    OrganisationDivisionSetAdmin,
)
from organisations.views.admin.organisation_geography import (
    OrganisationGeographyAdmin,
)
from organisations.views.admin.organisation_geography_problem import (
    OrganisationGeographyProblemAdmin,
)
from organisations.views.admin.organisation_problem import (
    OrganisationProblemAdmin,
)

# TODO: should this live here?
#     (Talking about the model admin and other added classes)
#     The other admins live in views.admin, but that's not very typical for Django
#     This is more like Django, but less like the project.


class ReadyForProcessingListFilter(SimpleListFilter):
    title = "Ready for processing"
    parameter_name = "ready_for_processing"

    def lookups(self, request, model_admin):
        return [(True, "Yes"), (False, "No")]

    def queryset(self, request, queryset):
        # TODO: Check / implement this logic
        if self.value():
            return queryset.unprocessed()
        return queryset


class WriteCSVToS3AdminForm(forms.Form):
    overwrite = forms.BooleanField(required=False)


class WriteCSVToS3(FormView):
    template_name = "admin/organisations/organisationboundaryreview/write_csv_to_s3_confirm.html"
    form_class = WriteCSVToS3AdminForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lgbce_helper = LGBCEReviewHelper()
        review = OrganisationBoundaryReview.objects.get(
            pk=self.kwargs["object_id"]
        )
        context["object"] = review
        end_date_rows = lgbce_helper.make_end_date_rows(
            review, str(review.effective_date)
        )
        context["end_date_header"] = end_date_rows[0]
        context["end_date_row"] = end_date_rows[1]
        ward_rows = lgbce_helper.get_eco_csv_rows(review)
        context["ward_rows"] = [row.values() for row in ward_rows]
        context["ward_header"] = ward_rows[0].keys()
        context["ward_count"] = len(ward_rows)
        context["review_bucket"] = lgbce_helper.review_bucket
        return context

    def form_valid(self, form):
        context = self.get_context_data(**self.kwargs)
        review = context["object"]
        overwrite = form.cleaned_data["overwrite"]
        lgbce_helper = LGBCEReviewHelper(overwrite=overwrite)
        lgbce_helper.upload_boundaries_to_s3(review)
        lgbce_helper.upload_end_date_csv_to_s3(
            review, f"{review.effective_date:%Y-%m-%d}"
        )
        lgbce_helper.upload_eco_csv_to_s3(review)

        return HttpResponseRedirect(
            reverse(
                "admin:organisations_organisationboundaryreview_change",
                kwargs={"object_id": context["object"].pk},
            )
        )


class OrganisationBoundaryReviewAdmin(admin.ModelAdmin):
    # List view
    search_fields = ("organisation__common_name", "slug")
    list_display = ("lgbce_review_title", "status", "latest_event")
    list_filter = (ReadyForProcessingListFilter, "status", "latest_event")
    list_select_related = ["organisation"]

    # Detail view
    raw_id_fields = ("organisation", "divisionset")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/write_csv_to_s3/",
                self.admin_site.admin_view(WriteCSVToS3.as_view()),
                name="write_csv_to_s3_view",
            )
        ]
        return custom_urls + urls


admin.site.register(OrganisationBoundaryReview, OrganisationBoundaryReviewAdmin)

admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationDivision, OrganisationDivisionAdmin)
admin.site.register(OrganisationDivisionSet, OrganisationDivisionSetAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
admin.site.register(DivisionProblem, DivisionProblemAdmin)
admin.site.register(OrganisationProblem, OrganisationProblemAdmin)
admin.site.register(
    OrganisationGeographyProblem, OrganisationGeographyProblemAdmin
)
