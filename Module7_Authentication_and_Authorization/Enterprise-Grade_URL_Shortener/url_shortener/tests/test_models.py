from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from url_shortener.models import Click, Tag, Url

User = get_user_model()


class UserModelTest(TestCase):
    def test_defaults(self):
        user = User.objects.create_user(username="alice", email="alice@example.com", password="pw")
        self.assertFalse(user.is_premium)
        self.assertEqual(user.tier, User.Tier.FREE)


class UrlModelTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="alice", email="alice@example.com", password="pw")

    def test_create_url(self):
        url = Url.objects.create(
            original_url="https://www.example.com",
            short_code="abc123",
            owner=self.owner,
        )
        self.assertEqual(url.original_url, "https://www.example.com")
        self.assertEqual(url.short_code, "abc123")
        self.assertEqual(url.owner, self.owner)
        self.assertTrue(url.is_active)
        self.assertEqual(url.click_count, 0)

    def test_is_expired(self):
        future = Url.objects.create(
            original_url="https://a.com", short_code="fut001", owner=self.owner,
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )
        past = Url.objects.create(
            original_url="https://b.com", short_code="past001", owner=self.owner,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        self.assertFalse(future.is_expired())
        self.assertTrue(past.is_expired())

    def test_tags_many_to_many(self):
        url = Url.objects.create(original_url="https://a.com", short_code="tag001", owner=self.owner)
        marketing, _ = Tag.objects.get_or_create(name="Marketing")
        social, _ = Tag.objects.get_or_create(name="Social")
        url.tags.set([marketing, social])
        self.assertEqual(set(url.tags.all()), {marketing, social})
        self.assertIn(url, marketing.urls.all())


class UrlManagerTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="alice", email="alice@example.com", password="pw")

    def test_active_urls_excludes_inactive_and_expired(self):
        Url.objects.create(original_url="https://a.com", short_code="active1", owner=self.owner)
        Url.objects.create(
            original_url="https://b.com", short_code="inactiv1", owner=self.owner, is_active=False
        )
        Url.objects.create(
            original_url="https://c.com", short_code="expired1", owner=self.owner,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )

        active_codes = set(Url.objects.active_urls().values_list("short_code", flat=True))
        self.assertEqual(active_codes, {"active1"})

    def test_expired_urls(self):
        Url.objects.create(
            original_url="https://c.com", short_code="expired1", owner=self.owner,
            expires_at=timezone.now() - timezone.timedelta(days=1),
        )
        Url.objects.create(original_url="https://a.com", short_code="active1", owner=self.owner)

        expired_codes = set(Url.objects.expired_urls().values_list("short_code", flat=True))
        self.assertEqual(expired_codes, {"expired1"})

    def test_popular_urls_ordered_by_click_count(self):
        low = Url.objects.create(
            original_url="https://a.com", short_code="low0001", owner=self.owner, click_count=1
        )
        high = Url.objects.create(
            original_url="https://b.com", short_code="high001", owner=self.owner, click_count=10
        )
        self.assertEqual(list(Url.objects.popular_urls()), [high, low])


class ClickModelTest(TestCase):
    def test_create_click(self):
        owner = User.objects.create_user(username="bob", email="bob@example.com", password="pw")
        url = Url.objects.create(original_url="https://a.com", short_code="click01", owner=owner)
        click = Click.objects.create(
            url=url, ip_address="127.0.0.1", country="US", city="NYC", user_agent="pytest",
        )
        self.assertEqual(click.url, url)
        self.assertIn(click, url.clicks.all())
