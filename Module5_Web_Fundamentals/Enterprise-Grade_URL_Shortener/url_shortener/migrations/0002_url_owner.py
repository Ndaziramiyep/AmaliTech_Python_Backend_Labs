import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("url_shortener", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="url",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="urls",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]
