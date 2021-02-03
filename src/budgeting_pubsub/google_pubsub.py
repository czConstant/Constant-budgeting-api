import json
import logging

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from google.auth import jwt
from google.cloud import pubsub_v1

from budgeting_pubsub.constants import TASK, RECEIVED_TASK
from budgeting_pubsub.models import SubLog
from integration_3rdparty.const_budgeting import ConstantBudgetingManagement

service_account_info = json.load(open(settings.DJANGO_ROOT + "/settings/constant.json"))
audience = "https://pubsub.googleapis.com/google.pubsub.v1.Subscriber"

credentials = jwt.Credentials.from_service_account_info(
    service_account_info, audience=audience
)

# The same for the publisher, except that the "audience" claim needs to be adjusted
publisher_audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
credentials_pub = credentials.with_claims(audience=publisher_audience)
publisher = pubsub_v1.PublisherClient(credentials=credentials_pub)
subscriber = pubsub_v1.SubscriberClient(credentials=credentials)

topic_path = publisher.topic_path(service_account_info['project_id'], settings.PUBSUB['TOPIC_ID'])
email_topic_path = publisher.topic_path(service_account_info['project_id'], settings.PUBSUB['EMAIL_TOPIC_ID'])

subscription_path_exchange = \
    subscriber.subscription_path(service_account_info['project_id'], settings.PUBSUB['EXCHANGE_SUB_ID'])
subscription_path_saving = \
    subscriber.subscription_path(service_account_info['project_id'], settings.PUBSUB['SAVING_SUB_ID'])
subscription_path_backend = \
    subscriber.subscription_path(service_account_info['project_id'], settings.PUBSUB['BACKEND_SUB_ID'])
subscription_path_budgeting = \
    subscriber.subscription_path(service_account_info['project_id'], settings.PUBSUB['BUDGETING_SUB_ID'])


class PubSub:
    @staticmethod
    def send_message(user_id, t, data):
        msg = json.dumps({
            'UserID': user_id,
            'Type': t,
            'Data': data,
        }, cls=DjangoJSONEncoder)
        msg = msg.encode("utf-8")
        future = publisher.publish(topic_path, msg)
        return future

    @staticmethod
    def send_email_message(data):
        msg = json.dumps(data, cls=DjangoJSONEncoder)
        msg = msg.encode("utf-8")
        future = publisher.publish(email_topic_path, msg)
        return future

    @staticmethod
    def receive_message(subscription_path, max_messages=5):
        response = subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": max_messages,
            }
        )

        messages = []
        for msg in response.received_messages:
            messages.append(msg.message.data)

        ack_ids = [msg.ack_id for msg in response.received_messages]
        if ack_ids:
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids,
                }
            )

        return messages

    @staticmethod
    def receive_message_exchange():
        return PubSub.receive_message(subscription_path_exchange)

    @staticmethod
    def receive_message_saving():
        return PubSub.receive_message(subscription_path_saving)

    @staticmethod
    def receive_message_backend():
        return PubSub.receive_message(subscription_path_backend)

    @staticmethod
    def receive_message_budgeting():
        return PubSub.receive_message(subscription_path_budgeting)

    @staticmethod
    def async_receive_message(subscription_path, callback):
        private_subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
        streaming_pull_future = private_subscriber.subscribe(subscription_path, callback=callback)
        with private_subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result(timeout=55)
            except Exception:
                streaming_pull_future.cancel()

    @staticmethod
    def async_receive_message_budgeting():
        def inner_callback(message):
            try:
                data = None
                try:
                    data = json.loads(message.data)
                except Exception:
                    message.ack()

                if data and 'Type' in data and data['Type'] in RECEIVED_TASK:
                    SubLog.objects.get_or_create(
                        user_id=data['UserID'],
                        task=data['Type'],
                        message_id=message.message_id, defaults={'data': data}
                    )
                    ConstantBudgetingManagement.send_pubsub_task(data['Type'], message.message_id, data['Data'])
                # Ack if is able to send the message
                message.ack()
            except Exception as ex:
                logging.exception(ex)

        return PubSub.async_receive_message(subscription_path_budgeting, inner_callback)
