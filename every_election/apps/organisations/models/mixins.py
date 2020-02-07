from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date


class DateDisplayMixin:
    @property
    def active_period_text(self):
        text = f"{self.start_date.strftime('%d %b %Y')}"
        if self.end_date:
            return f"{text} to {self.end_date.strftime('%d %b %Y')}"
        else:
            return f"{text} onwards"


class DateConstraintMixin:
    def check_start_date(self):
        if type(self.start_date) == str:
            self.start_date = parse_date(self.start_date)
        if (
            self.start_date
            and self.organisation.start_date
            and self.start_date < self.organisation.start_date
        ):
            raise ValidationError(
                "start_date (%s) must be on or after parent organisation start_date (%s)"
                % (
                    self.start_date.isoformat(),
                    self.organisation.start_date.isoformat(),
                )
            )

    def check_end_date(self):
        if type(self.end_date) == str:
            self.end_date = parse_date(self.end_date)
        if (
            self.end_date
            and self.organisation.end_date
            and self.end_date > self.organisation.end_date
        ):
            raise ValidationError(
                "end_date (%s) must be on or before parent organisation end_date (%s)"
                % (self.end_date.isoformat(), self.organisation.end_date.isoformat())
            )
