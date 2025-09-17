from django import forms
from django.contrib import admin
from organisations.models import OrganisationDivision, OrganisationDivisionSet


class OrganisationDivisionSetAdminForm(forms.ModelForm):
    class Meta:
        model = OrganisationDivisionSet
        fields = (
            "organisation",
            "start_date",
            "end_date",
            "legislation_url",
            "consultation_url",
            "short_title",
            "notes",
        )


class OrganisationDivisionInlineAdmin(admin.TabularInline):
    model = OrganisationDivision
    extra = False
    readonly_fields = (
        "name",
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

    def get_readonly_fields(self, request, obj=None):
        # Only show pmtiles_md5_hash as readonly on the change (detail) view
        if obj:
            return ("pmtiles_md5_hash",)
        return ()
