import json
import logging
import os
from typing import Dict, Optional

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


def event_bus_exists(events_client, event_bus_arn: str) -> bool:
    """
    Check if the specified event bus ARN exists.
    """
    response = events_client.list_event_buses()
    event_buses = response.get("EventBuses", [])
    return any(bus.get("Arn") == event_bus_arn for bus in event_buses)


def send_event(detail: Dict, detail_type: str, source: Optional[str] = None):
    if not settings.SEND_EVENTS:
        logger.info(f"Skipping {detail_type} because SEND_EVENTS is disabled.")
        # don't attempt to push anything in local dev/under test
        return

    if source is None:
        source = f"everyelection-{settings.DC_ENVIRONMENT}-{settings.EC2_IP}"

    session = boto3.Session(
        region_name=os.environ.get("AWS_REGION", "eu-west-2")
    )
    events_client = session.client("events")

    event_bus_arn = settings.DC_EVENTBUS_ARN

    # Check if the event bus exists before sending events
    if not event_bus_exists(events_client, event_bus_arn):
        logger.error(
            f"Event bus {event_bus_arn} does not exist. Event will be dropped.",
            extra={"detail_type": detail_type, "source": source},
        )
        return

    try:
        response = events_client.put_events(
            Entries=[
                {
                    "Source": source,
                    "DetailType": detail_type,
                    "Detail": json.dumps(detail),
                    "EventBusName": event_bus_arn,
                }
            ]
        )
        if response["FailedEntryCount"] > 0:
            logger.error(
                "Event was unsuccessfully ingested.",
                extra={"response": response},
            )
    except (
        # Only exception listed in the boto3 put_events docs.
        events_client.exceptions.InternalException,
    ) as put_events_exception:
        # We don't want to break whatever operation we were trying to do when sending the message.
        # But we do want to tell sentry about it.
        logger.error(
            f"Failed to send event: {str(put_events_exception)}",
            exc_info=True,
            stack_info=True,
        )
