from django.contrib import admin
from django import forms
from datetime import datetime
from organisations.models import Organisation, OrganisationDivision
from .common import CustomOrganisationChoiceField


class CurrentDivisionFilter(admin.SimpleListFilter):
    title = "Current Divisions"
    parameter_name = "is_current"

    def lookups(self, request, model_admin):
        return (("true", "Current Divisions"),)

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter_by_date(datetime.today())
        else:
            return queryset


class TempIdFilter(admin.SimpleListFilter):
    title = "With Temp ID"
    parameter_name = "has_temp_id"

    def lookups(self, request, model_admin):
        return (("true", "With Temp ID"),)

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter_with_temp_id()
        else:
            return queryset


class OrganisationDivisionAdminForm(forms.ModelForm):
    organisation = CustomOrganisationChoiceField(queryset=Organisation.objects.all())

    class Meta:
        model = OrganisationDivision
        fields = "__all__"


class OrganisationDivisionAdmin(admin.ModelAdmin):
    list_display = ("official_identifier", "name", "organisation", "divisionset")
    ordering = ("organisation", "divisionset", "name")
    search_fields = ("official_identifier", "name")
    list_filter = [CurrentDivisionFilter, TempIdFilter, "division_type"]
    form = OrganisationDivisionAdminForm

    def get_queryset(self, request):
        return super().get_queryset(request).defer("geography")
