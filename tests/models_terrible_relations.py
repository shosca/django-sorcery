# -*- coding: utf-8 -*-

from django_sorcery.db import databases


db = databases.get("terrible")


class Foo(db.Model):

    id1 = db.Column(db.Integer(), primary_key=True)
    id2 = db.Column(db.Integer(), primary_key=True)

    parent_id2 = db.Column(db.Integer())

    partial_parent = db.relationship(
        "Foo",
        foreign_keys=[parent_id2],
        primaryjoin=db.and_(id1 == id1, db.remote(id2) == db.foreign(parent_id2)),
        uselist=False,
    )

    class Meta:
        table_args = db.args(db.ForeignKeyConstraint(["id1", "parent_id2"], ["foo.id1", "foo.id2"], use_alter=True))


db.create_all()
