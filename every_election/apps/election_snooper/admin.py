from django.contrib import admin  # noqa
from .models import SnoopedElection


class SnoopedElectionAdmin(admin.ModelAdmin):
    search_fields = ("id",)
    readonly_fields = [
        field.name for field in SnoopedElection._meta.get_fields()
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(SnoopedElection, SnoopedElectionAdmin)
