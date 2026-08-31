import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from url_shortener.services.kafka_producer import KafkaEventPublisher


class KafkaEventPublisherTest(TestCase):
    def test_publish_sends_json_encoded_payload(self):
        fake_producer = MagicMock()
        with patch('url_shortener.services.kafka_producer._get_producer', return_value=fake_producer):
            KafkaEventPublisher().publish('url-clicks', {'url_id': 1})

        call = fake_producer.produce.call_args
        self.assertEqual(call.args[0], 'url-clicks')
        self.assertEqual(json.loads(call.kwargs['value']), {'url_id': 1})
        fake_producer.poll.assert_called_once_with(0)

    def test_publish_swallows_broker_errors(self):
        fake_producer = MagicMock()
        fake_producer.produce.side_effect = BufferError('queue full')
        with patch('url_shortener.services.kafka_producer._get_producer', return_value=fake_producer):
            KafkaEventPublisher().publish('url-clicks', {'url_id': 1})
