from django.contrib import admin
from datetime import datetime


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
