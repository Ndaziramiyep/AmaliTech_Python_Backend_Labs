import json
import logging
from functools import lru_cache

from confluent_kafka import Producer
from django.conf import settings

from url_shortener.domain.interfaces import EventPublisher

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_producer() -> Producer:
    return Producer({'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS})


class KafkaEventPublisher(EventPublisher):
    """Publishes JSON-encoded events to Kafka.

    Publish failures (broker unreachable, etc.) are logged rather than raised,
    so a Kafka outage never breaks the request that triggered the event.
    """

    def publish(self, topic: str, payload: dict) -> None:
        try:
            producer = _get_producer()
            producer.produce(topic, value=json.dumps(payload).encode('utf-8'))
            producer.poll(0)
        except Exception:
            logger.warning('Failed to publish event to Kafka topic %s', topic, exc_info=True)
