import json
import logging

from confluent_kafka import Consumer
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from url_shortener.models import Click, Url

logger = logging.getLogger(__name__)


def process_click_event(payload: dict) -> None:
    """Persist a single click event (as published by RedirectUrlView) as a Click row."""
    url_obj = Url.objects.filter(pk=payload['url_id']).first()
    if url_obj is None:
        logger.warning('Dropping click event for unknown url_id=%s', payload.get('url_id'))
        return

    Click.objects.create(
        url=url_obj,
        ip_address=payload['ip_address'],
        user_agent=payload.get('user_agent', ''),
        referrer=payload.get('referrer'),
        clicked_at=parse_datetime(payload['clicked_at']),
    )


class Command(BaseCommand):
    help = 'Consume click events from Kafka and persist them as Click rows.'

    def handle(self, *args, **options):
        consumer = Consumer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': settings.KAFKA_CONSUMER_GROUP,
            'auto.offset.reset': 'earliest',
        })
        consumer.subscribe([settings.KAFKA_CLICK_TOPIC])
        self.stdout.write(self.style.SUCCESS(f'Listening on topic "{settings.KAFKA_CLICK_TOPIC}"...'))

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    logger.error('Kafka consumer error: %s', msg.error())
                    continue

                try:
                    process_click_event(json.loads(msg.value()))
                except Exception:
                    logger.exception('Failed to process click event')
        except KeyboardInterrupt:
            pass
        finally:
            consumer.close()
