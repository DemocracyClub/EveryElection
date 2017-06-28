from django import forms

from .models import SnoopedElection


class ReviewElectionForm(forms.ModelForm):

    class Meta:
        model = SnoopedElection
        fields = ['status', ]
        widgets = {
            'status': forms.widgets.RadioSelect()
        }

