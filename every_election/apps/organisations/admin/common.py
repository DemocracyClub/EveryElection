from django import forms

class CustomOrganisationChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):
        return "{name} ({start} - {end})".format(
            name=obj.name, start=obj.start_date, end=obj.end_date)


invalid_sources = ('unknown', 'lgbce', '')
