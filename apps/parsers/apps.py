from django.apps import AppConfig


class ParsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.parsers"
    label = "parsers"
    verbose_name = "문서 파서"
