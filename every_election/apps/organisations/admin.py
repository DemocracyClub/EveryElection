from django import forms
from django.contrib import admin
from .models import Organisation


class CustomOrganisationChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "{name} ({start} - {end})".format(
            name=obj.name, start=obj.start_date, end=obj.end_date)


admin.site.register(Organisation, admin.ModelAdmin)
