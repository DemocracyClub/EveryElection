import logging
import os
from typing import Optional

import boto3

logger = logging.getLogger(__name__)


CURRENT_ELECTIONS_PARQUET_EVENT_QUEUE_URL = os.environ.get(
    "CURRENT_ELECTIONS_PARQUET_EVENT_QUEUE_URL"
)


def push_event_to_queue(
    message_body: Optional[str] = None, message_group_id: Optional[str] = None
):
    if message_body is None:
        message_body = "Rebuild triggered by EveryElection"
    if message_group_id is None:
        message_group_id = "elections_set_changed"
    sqs_client = boto3.client("sqs")

    try:
        sqs_client.send_message(
            QueueUrl=CURRENT_ELECTIONS_PARQUET_EVENT_QUEUE_URL,
            MessageBody=message_body,
            MessageGroupId=message_group_id,
        )
    except (
        # All exceptions listed in the boto3 send_message docs.
        sqs_client.exceptions.InvalidMessageContents,
        sqs_client.exceptions.UnsupportedOperation,
        sqs_client.exceptions.RequestThrottled,
        sqs_client.exceptions.QueueDoesNotExist,
        sqs_client.exceptions.InvalidSecurity,
        sqs_client.exceptions.KmsDisabled,
        sqs_client.exceptions.KmsInvalidState,
        sqs_client.exceptions.KmsNotFound,
        sqs_client.exceptions.KmsOptInRequired,
        sqs_client.exceptions.KmsThrottled,
        sqs_client.exceptions.KmsAccessDenied,
        sqs_client.exceptions.KmsInvalidKeyUsage,
        sqs_client.exceptions.InvalidAddress,
    ) as sqs_exception:
        # We don't want to break whatever operation we were trying to do when sending the message.
        # But we do want to tell sentry about it.
        logger.error(
            f"Failed to push event to SQS queue: {str(sqs_exception)}",
            exc_info=True,
            stack_info=True,
        )
