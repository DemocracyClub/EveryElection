from django.contrib import admin


class OrganisationAdmin(admin.ModelAdmin):
    search_fields = ("official_name", "common_name", "official_identifier")
