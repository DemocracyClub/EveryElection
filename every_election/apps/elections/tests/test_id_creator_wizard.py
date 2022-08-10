from email import contentmanager
import json
from django.test import TestCase
from django.urls import reverse
from elections.forms import ElectionDateForm


class TestIdCreatorWizard(TestCase, ElectionDateForm):
    def test_id_creator_by_step(self):
        step_1 = self.client.get("/id_creator/date/")
        self.assertEqual(step_1.status_code, 200)

        form_data = {
            "date-date_0": "01",
            "date-date_1": "01",
            "date-date_2": "2023",
            "id_creator_wizard-current_step": "date",
        }
        # go to the next step in the form
        step_2 = self.client.post("/id_creator/date/", form_data)
        self.assertEqual(step_2.url, "/id_creator/election_type/")
