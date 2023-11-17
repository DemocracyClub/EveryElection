from organisations.boundaries.boundary_bot.common import (
    SLACK_WEBHOOK_URL,
    is_eco,
)
from polling_bot.brain import SlackClient


class SlackHelper:
    def __init__(self):
        self.messages = []

    def append_new_review_message(self, record):
        self.messages.append(
            "New boundary review found for %s: %s"
            % (record["name"], record["consultation_url"])
        )

    def append_completed_review_message(self, record):
        self.messages.append(
            "Completed boundary review for %s: %s"
            % (record["name"], record["consultation_url"])
        )

    def append_event_message(self, record):
        message = "%s boundary review status updated to '%s': %s" % (
            record["name"],
            record["latest_event"],
            record["consultation_url"],
        )
        if is_eco(record["latest_event"]):
            message = ":rotating_light: " + message + " :alarm_clock:"
        self.messages.append(message)

    def post_messages(self):
        client = SlackClient(SLACK_WEBHOOK_URL)
        for message in self.messages:
            client.post_message(message)
