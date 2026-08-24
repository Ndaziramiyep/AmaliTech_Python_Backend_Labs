"""Seed the default set of tags new URLs can be categorized with."""

from django.db import migrations

DEFAULT_TAGS = ["Marketing", "Social", "Personal", "Business", "Development"]


def seed_default_tags(apps, schema_editor):
    """Create each default tag record if it does not already exist."""
    Tag = apps.get_model("tags", "Tag")
    for name in DEFAULT_TAGS:
        Tag.objects.get_or_create(name=name)


def remove_default_tags(apps, schema_editor):
    """Delete the default tag records created by this migration."""
    Tag = apps.get_model("tags", "Tag")
    Tag.objects.filter(name__in=DEFAULT_TAGS).delete()


class Migration(migrations.Migration):

    dependencies = [("tags", "0001_initial")]

    operations = [migrations.RunPython(seed_default_tags, remove_default_tags)]
