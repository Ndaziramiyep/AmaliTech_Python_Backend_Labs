from django.db import migrations

DEFAULT_TAGS = ["Marketing", "Social", "Personal", "Business", "Other"]


def seed_default_tags(apps, schema_editor):
    Tag = apps.get_model("url_shortener", "Tag")
    Tag.objects.bulk_create([Tag(name=name) for name in DEFAULT_TAGS], ignore_conflicts=True)


def remove_default_tags(apps, schema_editor):
    Tag = apps.get_model("url_shortener", "Tag")
    Tag.objects.filter(name__in=DEFAULT_TAGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("url_shortener", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_tags, remove_default_tags),
    ]
