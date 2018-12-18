from django.contrib import admin
from django import forms
from organisations.models import Organisation, OrganisationGeography
from .common import CustomOrganisationChoiceField


class OrganisationGeographyAdminForm(forms.ModelForm):
    organisation = CustomOrganisationChoiceField(
        queryset=Organisation.objects.all())

    class Meta:
        model = OrganisationGeography
        fields = '__all__'


class OrganisationGeographyAdmin(admin.ModelAdmin):
    search_fields = (
        'gss',
        'organisation__official_name',
        'organisation__common_name',
        'organisation__official_identifier'
    )
    exclude = ('geography',)
    form = OrganisationGeographyAdminForm

    def get_queryset(self, request):
        return super().get_queryset(request).defer('geography')
