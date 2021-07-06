import json
from copy import deepcopy
from django import forms
from django.contrib import admin
from django.forms.widgets import Textarea
from django_markdown.admin import MarkdownModelAdmin
from .models import (
    ElectedRole,
    Election,
    Explanation,
    MetaData,
    ModerationHistory,
    ModerationStatuses,
)


def mark_current(modeladmin, request, queryset):
    queryset.update(current=True)


mark_current.short_description = "Mark selected elections as 'current'"


def mark_not_current(modeladmin, request, queryset):
    queryset.update(current=False)


mark_not_current.short_description = "Mark selected elections as not 'current'"


def unset_current(modeladmin, request, queryset):
    queryset.update(current=None)


unset_current.short_description = "Unset 'current'"


def soft_delete(modeladmin, request, queryset):
    """
    Admin action to bulk create a ModerationHistory object with a
    deleted status:
    https://github.com/DemocracyClub/EveryElection/wiki/Cancelled-Elections-and-Soft-Deletes
    """
    for election in queryset:
        ModerationHistory.objects.create(
            status_id=ModerationStatuses.deleted.value,
            election=election,
            user=request.user,
            notes="Bulk deleted via admin action",
        )


soft_delete.short_description = "Soft delete"


class ElectionAdmin(admin.ModelAdmin):

    search_fields = ("election_id",)

    def has_add_permission(self, request):
        return False

    readonly_fields = (
        "election_id",
        "tmp_election_id",
        "election_type",
        "election_subtype",
        "poll_open_date",
        "organisation",
        "elected_role",
        "division",
        "group",
        "moderation_status",
    )
    exclude = (
        "geography",
        "division_geography",
        "organisation_geography",
        "notice",
        "cancellation_notice",
    )
    list_filter = ["current"]
    list_display = ["election_id", "poll_open_date", "current", "moderation_status"]
    actions = [mark_current, mark_not_current, unset_current, soft_delete]
    date_hierarchy = "poll_open_date"

    def get_readonly_fields(self, request, obj=None):
        if obj.identifier_type == "ballot":
            return self.readonly_fields
        else:
            return self.readonly_fields + ("cancelled",)

    def render_change_form(self, request, context, *args, **kwargs):
        context["adminform"].form.fields["replaces"].queryset = (
            Election.public_objects.filter(cancelled=True)
            .filter(poll_open_date__lte=context["original"].poll_open_date)
            .filter(division_id=context["original"].division_id)
            .filter(organisation_id=context["original"].organisation_id)
        )
        return super().render_change_form(request, context, *args, **kwargs)

    def has_delete_permission(self, request, obj=None):
        """
        Disabled the built-in hard "delete" action. Instead the soft
        delete action should be used.
        """
        return False


class JSONEditor(Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        # if its valid json, pretty print it
        # if not (e.g: on init, validation error)
        # just use the input string
        try:
            value = json.dumps(json.loads(value), sort_keys=True, indent=4)
        finally:
            return super().render(name, value, attrs)


class MetaDataAdmin(admin.ModelAdmin):
    def get_form(self, *args, **kwargs):
        self.form = deepcopy(self.form)
        form = super().get_form(*args, **kwargs)
        form.base_fields["data"].widget = JSONEditor()
        return form


class ElectedRoleAdminForm(forms.ModelForm):
    class Meta:
        model = ElectedRole
        fields = "__all__"


class ElectedRoleAdmin(admin.ModelAdmin):
    search_fields = (
        "elected_title",
        "elected_role_name",
        "organisation__official_name",
        "organisation__common_name",
        "organisation__official_identifier",
    )
    form = ElectedRoleAdminForm


class ModerationHistoryAdmin(admin.ModelAdmin):

    list_display = ("election", "status", "user", "notes", "created")
    list_filter = ("status", "user")
    search_fields = ("election__election_id",)
    raw_id_fields = ("election",)
    date_hierarchy = "election__poll_open_date"
    readonly_fields = ["created", "modified"]

    # This makes ModerationHistory an append-only log in /admin.
    # We can add a new entry to the log, but
    # we can't edit or delete existing entries.
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(ElectedRole, ElectedRoleAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Explanation, MarkdownModelAdmin)
admin.site.register(MetaData, MetaDataAdmin)
admin.site.register(ModerationHistory, ModerationHistoryAdmin)
