import json
from copy import deepcopy

from django import forms
from django.contrib import admin
from django.db import models
from django.db.models import Manager
from django.forms.widgets import Textarea

from .baker import send_event
from .models import (
    ElectedRole,
    Election,
    Explanation,
    MetaData,
    ModerationHistory,
    ModerationStatuses,
)


class GroupTypeListFilter(admin.SimpleListFilter):
    """
    Elections without a group type are considered "ballots".
    Becuase "ballot" is implied only, this class is used to override
    the "-" option in the admin panel filters and make it read "ballot".
    """

    title = "group type"
    parameter_name = "group_type"

    def lookups(self, request, model_admin):
        return [
            ("ballot", "Ballot"),
            ("election", "Election"),
            ("organisation", "Organisation"),
            ("subtype", "Subtype"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "ballot":
            return queryset.filter(
                group_type=None,
            )

        return queryset.filter(
            group_type=self.value(),
        )


class ByElectionFilter(admin.SimpleListFilter):
    title = "contest type"
    parameter_name = "contest_type"

    def lookups(self, request, model_admin):
        return [
            ("by_election", "By Election"),
            ("scheduled_election", "Scheduled Election"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "by_election":
            return queryset.filter(election_id__contains=".by.")

        if self.value() == "scheduled_election":
            return queryset.exclude(election_id__contains=".by.")

        return queryset


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
        mh = ModerationHistory(
            status_id=ModerationStatuses.deleted.value,
            election=election,
            user=request.user,
            notes="Bulk deleted via admin action",
        )
        mh.save(push_event=False)
    send_event(
        detail={"description": "Admin soft delete"},
        detail_type="elections_set_changed",
    )


soft_delete.short_description = "Soft delete"


class ElectionAdmin(admin.ModelAdmin):
    search_fields = ("election_id",)

    fieldsets = (
        (
            "Election Information",
            {
                "fields": (
                    "election_id",
                    "election_title",
                    "explanation",
                    "friendly_group_type",
                    "group",
                )
            },
        ),
        (
            "Ballot Information",
            {
                "fields": (
                    "current",
                    "cancelled",
                    "cancellation_reason",
                    "seats_contested",
                    "seats_total",
                    "replaces",
                    "requires_voter_id",
                    "voting_system",
                    "metadata",
                ),
            },
        ),
        (
            "Source Information",
            {
                "fields": (
                    "source",
                    "snooped_election",
                ),
            },
        ),
        (
            "Internal Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    "organisation",
                    "division",
                    "tags",
                    "elected_role",
                    "poll_open_date",
                    "election_subtype",
                    "election_type",
                    "modified",
                    "created",
                    "current_status_display",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    readonly_fields = (
        "election_id",
        "friendly_group_type",
        "group",
        "seats_total",
        "snooped_election",
        "organisation",
        "division",
        "tags",
        "elected_role",
        "poll_open_date",
        "election_subtype",
        "election_type",
        "modified",
        "created",
        "current_status_display",
    )
    list_filter = [
        "current",
        "cancelled",
        GroupTypeListFilter,
        ByElectionFilter,
        "by_election_reason",
    ]
    list_display = [
        "election_id",
        "poll_open_date",
        "current",
        "current_status_display",
    ]
    actions = [mark_current, mark_not_current, unset_current, soft_delete]
    date_hierarchy = "poll_open_date"

    def friendly_group_type(self, obj):
        return obj.group_type or "ballot"

    friendly_group_type.short_description = "Group type"

    def get_readonly_fields(self, request, obj=None):
        if obj.identifier_type == "ballot":
            return self.readonly_fields
        return self.readonly_fields + ("cancelled",)

    def get_fieldsets(self, request, obj=None):
        if obj.group_type:
            # Hide Ballot Information section if not a ballot
            return tuple(
                f for f in self.fieldsets if f[0] != "Ballot Information"
            )
        if ".by." in obj.election_id:
            for fieldset_name, fieldset in self.fieldsets:
                if fieldset_name == "Ballot Information":
                    fieldset["fields"] += ("by_election_reason",)

        return self.fieldsets

    def render_change_form(self, request, context, *args, **kwargs):
        if context["adminform"].form.fields.get("replaces"):
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

    def current_status_display(self, obj):
        return obj.current_status

    current_status_display.short_description = "Current Status"


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
        form.base_fields[
            "data"
        ].help_text = "Meta Data should only be added to an election in exceptional circumstances and should not repeat existing template text."
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


class ExplanationAdminForm(forms.ModelForm):
    class Meta:
        model = Explanation
        fields = "__all__"

        widgets = {"explanation": admin.widgets.AdminTextareaWidget}

    def save(self, commit=True):
        """
        Call save() on each election the explainer is
        attached to. This is a simple way to ensure that
        these elections will be marked as updated when
        querying the API for recently updated elections.

        """

        model: Explanation = super().save(commit)
        model.save()
        for election in model.election_set.all():
            election.save()
        return model


class ExplanationAdmin(admin.ModelAdmin):
    form = ExplanationAdminForm


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


class ElectionStatusProblemManager(Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        latest_statuses = models.Subquery(
            ModerationHistory.objects.filter(
                election_id=models.OuterRef("id"),
            )
            .order_by("-modified")
            .values("status")[:1]
        )
        return qs.annotate(latest_status=latest_statuses).exclude(
            latest_status=models.F("current_status")
        )


class ElectionStatusProblem(Election):
    objects = ElectionStatusProblemManager()

    class Meta:
        verbose_name_plural = "⚠️ Current status Problems"
        proxy = True


class ElectionStatusProblemAdmin(ElectionAdmin):
    list_display_links = None


admin.site.register(ElectedRole, ElectedRoleAdmin)
admin.site.register(Election, ElectionAdmin)
admin.site.register(Explanation, ExplanationAdmin)
admin.site.register(MetaData, MetaDataAdmin)
admin.site.register(ModerationHistory, ModerationHistoryAdmin)
admin.site.register(ElectionStatusProblem, ElectionStatusProblemAdmin)
