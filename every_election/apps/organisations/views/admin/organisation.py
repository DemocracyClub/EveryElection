from django.contrib import admin
from elections.models import Election


class ElectionForOrganisationInlineAdmin(admin.StackedInline):
    model = Election
    fields = ["election_id"]
    can_delete = False
    readonly_fields = ["election_id"]
    show_change_link = True
    extra = 0
    ordering = ["poll_open_date"]

    def has_add_permission(self, request, obj=None):
        return False


class OrganisationAdmin(admin.ModelAdmin):
    search_fields = ("common_name", "slug")
    list_display = ("common_name", "active_period_text", "organisation_type")
    list_filter = ("organisation_type", "territory_code", "election_types")
    readonly_fields = [
        "created",
        "modified",
        "official_identifier",
        "organisation_type",
        "territory_code",
        "organisation_subtype",
        "slug",
    ]

    inlines = [ElectionForOrganisationInlineAdmin]
