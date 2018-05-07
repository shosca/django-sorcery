# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from enum import Enum

from django_sorcery.db import databases
from django_sorcery.db.query import Query


db = databases.get("test")


COLORS = ["", "red", "green", "blue", "silver"]


class VehicleType(Enum):
    bus = "Bus"
    car = "Car"


class OwnerQuery(Query):
    pass


class Owner(db.Model):
    query_class = OwnerQuery

    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())


class Vehicle(db.Model):
    id = db.Column(db.Integer(), autoincrement=True, primary_key=True, doc="The primary key")
    name = db.Column(db.String(), doc="The name of the vehicle")
    type = db.Column(db.Enum(VehicleType), nullable=False)
    created_at = db.Column(db.DateTime())
    paint = db.Column(db.Enum(*COLORS, name="ck_colors"))
    is_used = db.Column(db.Boolean)

    owner = db.ManyToOne(Owner, backref="vehicles")

    @property
    def lower_name(self):
        return self.name.lower()


class Part(db.Model):
    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    vehicles = db.ManyToMany(Vehicle, backref="parts", table_name="vehicle_parts")


class Option(db.Model):
    id = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    vehicles = db.ManyToMany(Vehicle, backref=db.backref("options"), table_name="vehicle_options")


class CompositePkModel(db.Model):
    query_class = None

    id = db.Column(db.Integer(), primary_key=True)
    pk = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())

    is_active = db.Column(db.Boolean())

    active = db.queryproperty(is_active=True)


class DummyEnum(Enum):
    one = 1
    two = 2


Choices = ["three", "four"]


class AllKindsOfFields(db.Model):
    pk = db.Column(db.Integer(), primary_key=True)

    # flags
    boolean_notnull = db.Column(db.Boolean(), nullable=False)
    boolean = db.Column(db.Boolean())
    enum = db.Column(db.Enum(DummyEnum))
    enum_choice = db.Column(db.Enum(*Choices))

    # numbers
    bigint = db.Column(db.BIGINT())
    biginteger = db.Column(db.BigInteger())
    decimal = db.Column(db.DECIMAL())
    float = db.Column(db.Float())
    int = db.Column(db.INT())
    integer = db.Column(db.Integer())
    numeric = db.Column(db.Numeric())
    real = db.Column(db.REAL())
    smallint = db.Column(db.SMALLINT())
    smallinteger = db.Column(db.SmallInteger())

    # strings
    char = db.Column(db.CHAR())
    clob = db.Column(db.CLOB())
    nchar = db.Column(db.NCHAR())
    nvarchar = db.Column(db.NVARCHAR())
    string = db.Column(db.String())
    text = db.Column(db.Text())
    unicode = db.Column(db.Unicode())
    unicodetext = db.Column(db.UnicodeText())
    varchar = db.Column(db.VARCHAR())

    # dates, times and durations
    date = db.Column(db.Date())
    datetime = db.Column(db.DateTime())
    interval = db.Column(db.Interval())
    time = db.Column(db.Time())
    timestamp = db.Column(db.TIMESTAMP())

    # blobs
    binary = db.Column(db.Binary())
    blob = db.Column(db.BLOB())
    largebinary = db.Column(db.LargeBinary())
    varbinary = db.Column(db.VARBINARY())


class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __composite_values__(self):
        return self.x, self.y

    def __repr__(self):
        return "Point(x=%r, y=%r)" % (self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, Point) and other.x == self.x and other.y == self.y

    def __ne__(self, other):
        return not self.__eq__(other)


class Vertex(db.Model):

    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)

    x1 = db.Column(db.Integer())
    y1 = db.Column(db.Integer())
    x2 = db.Column(db.Integer())
    y2 = db.Column(db.Integer())

    start = db.composite(Point, x1, y1)
    end = db.composite(Point, x2, y2)


class ModelTwo(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())


class ModelOne(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    _model_twos = db.OneToMany(ModelTwo, backref="_model_one")


model_three_ones = db.Table(
    "model_three_ones",
    db.Column("model_one_pk", db.Integer(), db.ForeignKey("modelone.pk"), primary_key=True),
    db.Column("model_two_pk", db.Integer(), db.ForeignKey("modelthree.pk"), primary_key=True),
)


class ModelThree(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    model_ones = db.ManyToMany(ModelOne, secondary=model_three_ones)


class ModelFour(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    _model_twos = db.OneToMany(ModelTwo, backref=db.backref("_model_four"))


db.configure_mappers()
db.create_all()
