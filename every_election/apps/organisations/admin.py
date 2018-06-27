from django import forms
from django.contrib import admin
from .models import Organisation, OrganisationGeography


class CustomOrganisationChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "{name} ({start} - {end})".format(
            name=obj.name, start=obj.start_date, end=obj.end_date)

class OrganisationGeographyAdminForm(forms.ModelForm):
    organisation = CustomOrganisationChoiceField(
        queryset=Organisation.objects.all())

    class Meta:
        model = OrganisationGeography
        fields = '__all__'

class OrganisationGeographyAdmin(admin.ModelAdmin):
    exclude = ('geography',)
    form = OrganisationGeographyAdminForm


admin.site.register(Organisation, admin.ModelAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
