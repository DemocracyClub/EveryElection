import json
from copy import deepcopy
from django.contrib import admin
from django.forms.widgets import Textarea
from django_markdown.admin import MarkdownModelAdmin
from .models import Election, Explanation, MetaData


class ElectionAdmin(admin.ModelAdmin):

    search_fields = ('election_id',)

    def has_add_permission(self, request):
        return False

    readonly_fields = (
        'election_id',
        'tmp_election_id',
        'election_type',
        'election_subtype',
        'poll_open_date',
        'organisation',
        'elected_role',
        'division',
        'group',
    )
    exclude = (
        'geography',
        'division_geography',
        'organisation_geography',
    )


class JSONEditor(Textarea):
    def render(self, name, value, attrs=None):
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
        form.base_fields['data'].widget = JSONEditor()
        return form


admin.site.register(Election, ElectionAdmin)
admin.site.register(Explanation, MarkdownModelAdmin)
admin.site.register(MetaData, MetaDataAdmin)
