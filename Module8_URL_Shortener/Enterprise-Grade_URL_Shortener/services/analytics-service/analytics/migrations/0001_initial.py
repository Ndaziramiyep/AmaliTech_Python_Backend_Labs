from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClickEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("short_code", models.CharField(db_index=True, max_length=10)),
                ("owner_id", models.PositiveIntegerField(db_index=True)),
                ("referrer", models.CharField(blank=True, default="", max_length=500)),
                ("user_agent", models.CharField(blank=True, default="", max_length=500)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("clicked_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-clicked_at"],
            },
        ),
    ]
