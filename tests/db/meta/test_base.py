# -*- coding: utf-8 -*-

from django_sorcery.db import meta  # noqa

from ...base import TestCase
from ...testapp.models import Business


class TestModelMeta(TestCase):
    def test_model_meta(self):
        info = meta.model_info(Business)

        info_from_meta = meta.model_info(Business.__mapper__)

        info_from_instance = meta.model_info(Business())

        self.assertIs(info, info_from_meta)
        self.assertIs(info_from_meta, info_from_instance)
