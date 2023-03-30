from django import forms
from django.contrib import admin
from organisations.models import OrganisationGeographyProblem


class OrganisationGeographyProblemAdminForm(forms.ModelForm):
    class Meta:
        model = OrganisationGeographyProblem
        fields = "__all__"


class OrganisationGeographyProblemAdmin(admin.ModelAdmin):
    actions = None

    ordering = ("source", "gss", "start_date")
    list_display = ("__str__", "problem_text")
    readonly_fields = ("problem_text", "no_gss_code", "invalid_source", "no_geography")
    exclude = ("geography",)
    form = OrganisationGeographyProblemAdminForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).defer("geography")
