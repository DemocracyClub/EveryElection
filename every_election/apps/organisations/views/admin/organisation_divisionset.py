from django.contrib import admin
from django import forms

from organisations.models import OrganisationDivisionSet, OrganisationDivision


class OrganisationDivisionSetAdminForm(forms.ModelForm):
    class Meta:
        model = OrganisationDivisionSet
        fields = "__all__"


class OrganisationDivisionInlineAdmin(admin.TabularInline):
    model = OrganisationDivision
    extra = False
    readonly_fields = (
        "name",
        "official_identifier",
        "division_type",
        "division_subtype",
        "slug",
    )
    fields = (
        "name",
        "official_identifier",
        "seats_total",
        "slug",
        "division_type",
        "division_subtype",
    )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class OrganisationDivisionSetAdmin(admin.ModelAdmin):
    ordering = ("organisation", "start_date")
    search_fields = (
        "organisation__official_name",
        "organisation__common_name",
        "organisation__official_identifier",
        "short_title",
    )
    form = OrganisationDivisionSetAdminForm
    inlines = [
        OrganisationDivisionInlineAdmin,
    ]
