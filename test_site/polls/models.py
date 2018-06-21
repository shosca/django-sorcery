# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import databases


db = databases.get("default")


class Question(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    question_text = db.Column(db.String(length=200))
    pub_date = db.Column(db.DateTime())


class Choice(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    choice_text = db.Column(db.String(length=200))
    votes = db.Column(db.Integer(), default=0)

    question = db.ManyToOne(Question, backref=db.backref("choices", cascade="all, delete-orphan"))


db.configure_mappers()
db.create_all()
