from django import forms
from django.contrib import admin
from organisations.models import OrganisationGeography


class OrganisationGeographyAdminForm(forms.ModelForm):
    class Meta:
        model = OrganisationGeography
        fields = "__all__"


class OrganisationGeographyAdmin(admin.ModelAdmin):
    search_fields = (
        "gss",
        "organisation__official_name",
        "organisation__common_name",
        "organisation__official_identifier",
    )
    exclude = ("geography",)
    form = OrganisationGeographyAdminForm

    def get_queryset(self, request):
        return super().get_queryset(request).defer("geography")
