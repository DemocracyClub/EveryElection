from django.contrib import admin


class OrganisationProblemAdmin(admin.ModelAdmin):

    actions = None

    ordering = (
        "organisation_type",
        "organisation_subtype",
        "official_name",
        "start_date",
    )
    list_display = ("official_name", "start_date", "end_date", "problem_text")
    readonly_fields = (
        "problem_text",
        "no_geography",
        "no_divisionset",
        "no_electedrole",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
