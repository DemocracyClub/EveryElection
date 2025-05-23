import json
import logging
import os
from typing import Dict, Optional

import boto3
from django.conf import settings

logger = logging.getLogger(__name__)


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

    try:
        entries = [
            {
                "Source": source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "EventBusName": event_bus_arn,
            }
        ]
        response = events_client.put_events(
            Entries=entries,
        )
        if response["FailedEntryCount"] > 0:
            logger.error(
                f"send_event failed with {entries}",
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
