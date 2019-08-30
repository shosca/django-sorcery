# -*- coding: utf-8 -*-

from sqlalchemy.orm import configure_mappers

from django.apps import AppConfig


class PollsConfig(AppConfig):
    name = "polls"

    def ready(self):
        configure_mappers()
