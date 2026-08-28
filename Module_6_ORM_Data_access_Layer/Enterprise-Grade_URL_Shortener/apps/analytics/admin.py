"""Admin registration for the Click model."""

from django.contrib import admin

from .models import Click


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    """Provides a read-only admin list view for click analytics."""

    list_display = ["url", "ip_address", "country", "clicked_at"]
    list_filter = ["country", "clicked_at"]
    readonly_fields = [f.name for f in Click._meta.fields]
