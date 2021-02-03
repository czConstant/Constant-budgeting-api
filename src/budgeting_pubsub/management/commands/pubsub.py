import time

from django.core.management.base import BaseCommand

from exchange_pubsub.google_pubsub import PubSub


class Command(BaseCommand):
    help = 'Start to run pubsub'

    def handle(self, *args, **options):
        while True:
            PubSub.async_receive_message_budgeting()
            time.sleep(5)
