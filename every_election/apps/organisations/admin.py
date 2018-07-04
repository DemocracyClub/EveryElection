from django import forms
from django.contrib import admin
from .models import Organisation, OrganisationGeography


class CustomOrganisationChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "{name} ({start} - {end})".format(
            name=obj.name, start=obj.start_date, end=obj.end_date)


class OrganisationAdmin(admin.ModelAdmin):
    search_fields = ('official_name', 'common_name', 'official_identifier')


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


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
