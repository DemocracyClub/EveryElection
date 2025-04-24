import json
import os
from unittest.mock import MagicMock, patch

import boto3
import pytest
from botocore.exceptions import ClientError
from django.test import override_settings
from elections.baker import event_bus_exists, send_event
from moto import mock_aws

DEVS_DC_API_ACCOUNT_ID = "111111111111"
EE_ACCOUNT_ID = "123456789012"  # This is the moto default


@pytest.fixture
def devs_dc_moto_account_env(monkeypatch):
    monkeypatch.setenv("MOTO_ACCOUNT_ID", DEVS_DC_API_ACCOUNT_ID)


@pytest.fixture()
def devapi_boto_session(devs_dc_moto_account_env):
    with mock_aws():
        yield boto3.Session(
            region_name=os.environ.get("AWS_REGION", "eu-west-2")
        )


@pytest.fixture
def devapi_iam_client(devs_dc_moto_account_env):
    with mock_aws():
        yield boto3.client("iam")


@pytest.fixture()
def devapi_sqs_client(devs_dc_moto_account_env, devapi_boto_session):
    with mock_aws():
        yield devapi_boto_session.client("sqs")


@pytest.fixture()
def devapi_events_client(devs_dc_moto_account_env, devapi_boto_session):
    with mock_aws():
        yield devapi_boto_session.client("events")


@mock_aws
@pytest.fixture
def devapi_sqs_queue_details(devs_dc_moto_account_env, devapi_sqs_client):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "events.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": "*",
            }
        ],
    }
    queue = devapi_sqs_client.create_queue(
        QueueName="CurrentElectionsEventQueue.fifo",
        Attributes={
            "FifoQueue": "true",
            "ContentBasedDeduplication": "true",
            "Policy": json.dumps(policy),
        },
    )
    queue_url = queue["QueueUrl"]
    queue_attributes = devapi_sqs_client.get_queue_attributes(
        QueueUrl=queue_url, AttributeNames=["All"]
    )
    queue_arn = queue_attributes["Attributes"]["QueueArn"]
    return queue_url, queue_arn


@mock_aws
@pytest.fixture(autouse=True)
def devapi_eventbridge_rule(
    devs_dc_moto_account_env, devapi_events_client, devapi_sqs_queue_details
):
    _, queue_arn = devapi_sqs_queue_details
    eventpattern = {"detail-type": ["elections_set_changed"]}
    rule_name = "RebuildCurrentElectionsParquetTrigger"
    devapi_events_client.put_rule(
        Name=rule_name, State="ENABLED", EventPattern=json.dumps(eventpattern)
    )
    devapi_events_client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": "CurrentElectionsEventQueue.fifo",
                "Arn": queue_arn,
                "SqsParameters": {"MessageGroupId": "elections_set_changed"},
            }
        ],
    )


@pytest.fixture()
def devapi_event_bus_arn(devs_dc_moto_account_env, devapi_events_client):
    with mock_aws():
        r = devapi_events_client.list_event_buses()
        yield r["EventBuses"][0]["Arn"]


@pytest.fixture()
def org_wide_eventbus_role(devs_dc_moto_account_env, devapi_iam_client):
    with mock_aws():
        # Define the role name
        role_name = "EventsRole"

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": [
                        "events:DescribeEventBus",
                        "events:ListEventBuses",
                    ],
                    "Resource": "arn:aws:events:eu-west-2:*:event-bus/default",
                    "Effect": "Allow",
                }
            ],
        }

        trust_relationship = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {"aws:PrincipalOrgID": "foo-org-id"}
                    },
                }
            ],
        }

        response = devapi_iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_relationship),
        )

        devapi_iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName="EventsAccess",
            PolicyDocument=json.dumps(policy_document),
        )

        # Return the role arn
        yield response["Role"]["Arn"]


@pytest.mark.django_db
@override_settings(
    SEND_EVENTS=True,
    DC_ENVIRONMENT="development",
    EC2_IP="127.0.0.1",
)
def test_send_event_happy_path(
    devapi_sqs_client,
    devapi_sqs_queue_details,
    devapi_event_bus_arn,
    org_wide_eventbus_role,
):
    with override_settings(
        DC_EVENTBUS_ARN=devapi_event_bus_arn,
        DC_CHECK_EVENTBUS_ROLE=org_wide_eventbus_role,
    ):
        queue_url, _ = devapi_sqs_queue_details
        detail = {"message": "Test event"}
        detail_type = "elections_set_changed"

        with patch("elections.baker.logger") as mock_logger:
            send_event(detail, detail_type)

        sqs_response = devapi_sqs_client.receive_message(
            QueueUrl=queue_url, WaitTimeSeconds=5
        )
        assert "Messages" in sqs_response
        assert (
            json.loads(sqs_response["Messages"][0]["Body"])["source"]
            == "everyelection-development-127.0.0.1"
        )
        mock_logger.error.assert_not_called()


@pytest.mark.django_db
@override_settings(
    SEND_EVENTS=True,
    DC_ENVIRONMENT="development",
    EC2_IP="127.0.0.1",
)
def test_send_event_no_eventbus_arn(
    devapi_sqs_client, devapi_sqs_queue_details, devapi_event_bus_arn
):
    queue_url, _ = devapi_sqs_queue_details
    detail = {"message": "Test event"}
    detail_type = "elections_set_changed"

    with pytest.raises(AttributeError):
        send_event(detail, detail_type)


@pytest.mark.django_db
@override_settings(
    SEND_EVENTS=False,
    DC_ENVIRONMENT="development",
    EC2_IP="127.0.0.1",
)
def test_send_event_disabled(
    devapi_sqs_client,
    devapi_sqs_queue_details,
    devapi_event_bus_arn,
    org_wide_eventbus_role,
):
    # Even with all other settings set, `SEND_EVENTS=False` should still stop events being sent.
    with override_settings(
        DC_EVENTBUS_ARN=devapi_event_bus_arn,
        DC_CHECK_EVENTBUS_ROLE=org_wide_eventbus_role,
    ):
        queue_url, _ = devapi_sqs_queue_details
        detail = {"message": "Test event"}
        detail_type = "elections_set_changed"

        with patch("elections.baker.logger") as mock_logger:
            send_event(detail, detail_type)

        sqs_response = devapi_sqs_client.receive_message(
            QueueUrl=queue_url, WaitTimeSeconds=5
        )
        assert "Messages" not in sqs_response
        mock_logger.info.assert_called_once()
        # Check if the message is correct
        info_message = mock_logger.info.call_args[0][0]
        assert (
            info_message
            == "Skipping elections_set_changed because SEND_EVENTS is disabled."
        )
        mock_logger.error.assert_not_called()


@pytest.mark.django_db
@override_settings(
    SEND_EVENTS=True,
    DC_ENVIRONMENT="development",
    EC2_IP="127.0.0.1",
)
def test_send_event_internal_exception(
    devapi_event_bus_arn, org_wide_eventbus_role
):
    """Test that the InternalException in send_event is properly caught and logged."""
    with override_settings(
        DC_EVENTBUS_ARN=devapi_event_bus_arn,
        DC_CHECK_EVENTBUS_ROLE=org_wide_eventbus_role,
    ):
        detail = {"message": "Test event with client exception"}
        detail_type = "elections_set_changed"

        with (
            patch("elections.baker.event_bus_exists", return_value=True),
            patch("elections.baker.boto3.Session") as mock_session_class,
        ):
            mock_put_events = MagicMock(
                side_effect=ClientError(
                    error_response={
                        "Error": {
                            "Code": "InternalException",
                            "Message": "OH NO. Something went wrong.",
                        }
                    },
                    operation_name="PutEvents",
                )
            )

            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            mock_client = MagicMock()
            mock_session.client.return_value = mock_client

            mock_client.put_events = mock_put_events

            # The mock client also needs an exceptions attribute with an InternalException
            # that matches what's expected in the except clause
            mock_client.exceptions = MagicMock()
            mock_client.exceptions.InternalException = ClientError

            # Patch the logger to verify it gets called
            with patch("elections.baker.logger") as mock_logger:
                # Test the function - it should handle the exception internally
                send_event(detail, detail_type)

                # Verify the logger.error was called as expected
                mock_logger.error.assert_called_once()
                # Check if the error message is correct
                error_message = mock_logger.error.call_args[0][0]
                assert (
                    "Failed to send event" in error_message
                )  # from our function
                assert (
                    "OH NO. Something went wrong" in error_message
                )  # from our mock

                # Check if the logger was called with the correct kwargs
                call_kwargs = mock_logger.error.call_args[1]
                assert call_kwargs["exc_info"] is True
                assert call_kwargs["stack_info"] is True


@pytest.mark.django_db
def test_event_bus_exists(devapi_event_bus_arn, org_wide_eventbus_role):
    with override_settings(
        DC_EVENTBUS_ARN=devapi_event_bus_arn,
        DC_CHECK_EVENTBUS_ROLE=org_wide_eventbus_role,
    ):
        assert event_bus_exists(devapi_event_bus_arn) is True
        assert event_bus_exists("DoesNotExist") is False
