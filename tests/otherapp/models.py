# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import databases


db = databases.get("test")


class OtherAppModel(db.Model):

    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())


class OtherAppInOtherApp(db.Model):

    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    class Meta:
        app_label = "tests.testapp"


db.configure_mappers()
db.create_all()
