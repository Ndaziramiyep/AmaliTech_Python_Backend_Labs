import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from url_shortener.management.commands.consume_click_events import process_click_event
from url_shortener.models import Click, Url
from url_shortener.services.kafka_producer import KafkaEventPublisher

User = get_user_model()


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


class ProcessClickEventTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carol', email='carol@example.com', password='pw')
        self.url_obj = Url.objects.create(original_url='https://a.com', short_code='abc123', owner=self.user)

    def test_creates_click_row_from_event_payload(self):
        process_click_event({
            'url_id': self.url_obj.pk,
            'ip_address': '9.9.9.9',
            'user_agent': 'pytest-agent',
            'referrer': None,
            'clicked_at': '2026-08-31T10:00:00+00:00',
        })

        click = Click.objects.get(url=self.url_obj)
        self.assertEqual(click.ip_address, '9.9.9.9')
        self.assertEqual(click.user_agent, 'pytest-agent')
        self.assertIsNone(click.referrer)

    def test_drops_event_for_unknown_url(self):
        process_click_event({
            'url_id': 999999,
            'ip_address': '9.9.9.9',
            'user_agent': 'pytest-agent',
            'referrer': None,
            'clicked_at': '2026-08-31T10:00:00+00:00',
        })

        self.assertEqual(Click.objects.count(), 0)
