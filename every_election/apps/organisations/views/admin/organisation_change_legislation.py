from django.contrib import admin
from organisations.models import OrganisationChange


class OrganisationChangeInlineAdmin(admin.TabularInline):
    model = OrganisationChange
    extra = 0
    show_change_link = True
    fields = (
        "organisation",
        "change_type",
    )
    radio_fields = {"change_type": admin.HORIZONTAL}
    autocomplete_fields = ("organisation",)


class OrganisationChangeLegislationAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "effective_date",
        "legislation_made",
        "created",
        "modified",
    )
    list_filter = ("legislation_made", "effective_date")
    search_fields = ("legislation_title", "legislation_url", "consultation_url")
    inlines = (OrganisationChangeInlineAdmin,)


class OrganisationChangeAdmin(admin.ModelAdmin):
    list_display = (
        "change_type",
        "organisation",
        "effective_date",
        "organisation_change_legislation",
    )
    list_filter = (
        "organisation_change_legislation",
        "change_type",
    )
    search_fields = (
        "organisation__official_name",
        "organisation__common_name",
        "organisation__official_identifier",
        "organisation_change_legislation__legislation_title",
    )
    list_select_related = ("organisation", "organisation_change_legislation")
    readonly_fields = (
        "organisation_change_legislation",
        "organisation",
        "change_type",
    )

    @admin.display(description="Effective Date")
    def effective_date(self, obj):
        return obj.organisation_change_legislation.effective_date

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
