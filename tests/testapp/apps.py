from django.apps import AppConfig


class TestAppConfig(AppConfig):
    name = "tests.testapp"
    label = "tests_testapp"
    version_table_schema = "public"

    def ready(self):
        from .models import db

        db.configure_mappers()
        db.create_all()
