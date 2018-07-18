# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import databases


default_db = databases.get("default")
other_db = databases.get("fromdbs")


class Foo(default_db.Model):

    id = default_db.Column(default_db.Integer(), autoincrement=True, primary_key=True)
    name = default_db.Column(default_db.String(length=10), nullable=False)


class Bar(other_db.Model):

    id = other_db.Column(other_db.Integer(), autoincrement=True, primary_key=True)
    name = other_db.Column(other_db.String(length=10), nullable=False)


default_db.create_all()
other_db.create_all()
