from django import forms

from .models import SnoopedElection
from elections.models import ModerationHistory, ModerationStatus, ModerationStatuses


class ReviewElectionForm(forms.ModelForm):
    class Meta:
        model = SnoopedElection
        fields = ["status"]
        widgets = {"status": forms.widgets.RadioSelect()}


class ModerationHistoryForm(forms.ModelForm):
    class Meta:
        model = ModerationHistory
        fields = ["status"]
        widgets = {"status": forms.widgets.RadioSelect()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].queryset = ModerationStatus.objects.filter(
            short_label__in=[
                ModerationStatuses.approved.value,
                ModerationStatuses.suggested.value,
                ModerationStatuses.rejected.value,
            ]
        )
        self.fields["status"].empty_label = None
