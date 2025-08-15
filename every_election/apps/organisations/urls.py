from django.urls import re_path

from .views import (
    AllBoundaryReviewsView,
    DivisionsetDetailView,
    OrganisationDetailView,
    OrganisationsFilterView,
    SingleBoundaryReviewView,
    SupportedOrganisationsView,
)

urlpatterns = [
    re_path(
        r"^$", SupportedOrganisationsView.as_view(), name="organisations_view"
    ),
    # a list of all boundary reviews
    re_path(
        r"^boundary_reviews/$",
        AllBoundaryReviewsView.as_view(),
        name="boundary_reviews_view",
    ),
    # a single boundary review record
    re_path(
        r"^boundary_reviews/(?P<boundary_review_id>.+)/$",
        SingleBoundaryReviewView.as_view(),
        name="single_boundary_review_view",
    ),
    # divisionset detail page
    re_path(
        r"^divisionsets/(?P<divisionset_id>.+)/$",
        DivisionsetDetailView.as_view(),
        name="divset_detail_view",
    ),
    # canonical URL for a single organisation record
    re_path(
        r"^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/(?P<date>\d{4}-\d{2}-\d{2})/$",
        OrganisationDetailView.as_view(),
        name="organisation_view",
    ),
    # a list of 'generations' of an organisation
    re_path(
        r"^(?P<organisation_type>[-\w]+)/(?P<official_identifier>[-\w]+)/$",
        OrganisationsFilterView.as_view(),
        name="organisations_filter_by_identifier",
    ),
    # list of organisations of a given type
    re_path(
        r"^(?P<organisation_type>[-\w]+)/$",
        OrganisationsFilterView.as_view(),
        name="organisations_filter_by_type",
    ),
]
