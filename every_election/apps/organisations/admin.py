from datetime import datetime
from django import forms
from django.contrib import admin
from .models import (
    Organisation,
    OrganisationDivision,
    OrganisationGeography,
)


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


class CurrentDivisionFilter(admin.SimpleListFilter):
    title = 'Current Divisions'
    parameter_name = 'is_current'

    def lookups(self, request, model_admin):
       return (
          ('true', 'Current Divisions'),
       )

    def queryset(self, request, queryset):
      if self.value() == 'true':
          return queryset.filter_by_date(datetime.today())
      else:
          return queryset


class TempIdFilter(admin.SimpleListFilter):
    title = 'With Temp ID'
    parameter_name = 'has_temp_id'

    def lookups(self, request, model_admin):
       return (
          ('true', 'With Temp ID'),
       )

    def queryset(self, request, queryset):
      if self.value() == 'true':
          return queryset.filter_with_temp_id()
      else:
          return queryset


class OrganisationDivisionAdmin(admin.ModelAdmin):
    list_display = ('official_identifier', 'name', 'organisation', 'divisionset')
    ordering = ('organisation', 'divisionset', 'name')
    search_fields = ('official_identifier', 'name')
    list_filter = [CurrentDivisionFilter, TempIdFilter, 'division_type']


admin.site.register(Organisation, OrganisationAdmin)
admin.site.register(OrganisationDivision, OrganisationDivisionAdmin)
admin.site.register(OrganisationGeography, OrganisationGeographyAdmin)
