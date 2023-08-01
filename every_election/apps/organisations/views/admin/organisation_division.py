from datetime import datetime

from django import forms
from django.contrib import admin
from organisations.models import OrganisationDivision


class CurrentDivisionFilter(admin.SimpleListFilter):
    title = "Current Divisions"
    parameter_name = "is_current"

    def lookups(self, request, model_admin):
        return (("true", "Current Divisions"),)

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter_by_date(datetime.today())
        return queryset


class TempIdFilter(admin.SimpleListFilter):
    title = "With Temp ID"
    parameter_name = "has_temp_id"

    def lookups(self, request, model_admin):
        return (("true", "With Temp ID"),)

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter_with_temp_id()
        return queryset


class OrganisationDivisionAdminForm(forms.ModelForm):
    class Meta:
        model = OrganisationDivision
        fields = "__all__"


class OrganisationDivisionAdmin(admin.ModelAdmin):
    list_display = ("official_identifier", "name", "divisionset")
    ordering = ("divisionset", "name")
    search_fields = ("official_identifier", "name")
    list_filter = [CurrentDivisionFilter, TempIdFilter, "division_type"]
    form = OrganisationDivisionAdminForm
    readonly_fields = ["created", "modified"]

    def get_queryset(self, request):
        return super().get_queryset(request).defer("geography")
