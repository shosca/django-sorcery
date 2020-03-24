from django.apps import AppConfig
from sqlalchemy.orm import configure_mappers


class PollsConfig(AppConfig):
    name = "polls"

    def ready(self):
        configure_mappers()
