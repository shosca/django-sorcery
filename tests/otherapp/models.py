# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import databases


db = databases.get("test")


class OtherAppModel(db.Model):

    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())


db.configure_mappers()
db.drop_all()
db.create_all()
