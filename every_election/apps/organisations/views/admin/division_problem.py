from django import forms
from django.contrib import admin
from organisations.models import DivisionProblem


class DivisionProblemForm(forms.ModelForm):
    class Meta:
        model = DivisionProblem
        fields = "__all__"


class DivisionProblemAdmin(admin.ModelAdmin):
    actions = None

    ordering = ("divisionset", "name")
    list_display = (
        "official_identifier",
        "name",
        "divisionset",
        "problem_text",
    )
    readonly_fields = ("problem_text", "no_gss_code", "invalid_source", "no_geography")
    form = DivisionProblemForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).defer("geography")
