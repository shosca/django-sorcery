# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from enum import Enum

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from django_sorcery.db import databases
from django_sorcery.db.models import autocoerce, autocoerce_properties
from django_sorcery.db.query import Query
from django_sorcery.validators import ValidateTogetherModelFields, ValidateUnique


db = databases.get("test")


COLORS = ["", "red", "green", "blue", "silver", "pink"]


class VehicleType(Enum):
    bus = "Bus"
    car = "Car"


class States(Enum):
    NY = "NY"
    NJ = "NJ"


class OwnerQuery(Query):
    pass


def street_validator(value):
    if len(value) < 3:
        raise ValidationError({"street": "Street should be at least 2 characters."})


class Address(db.BaseComposite):
    street = db.CharField(length=300, validators=[street_validator])
    state = db.EnumField(choices=States, constraint_name="states")
    zip = db.CharField(length=15, validators=[RegexValidator(r"^\d+$")])

    validators = [ValidateTogetherModelFields(["street", "state", "zip"])]

    def clean_state(self):
        if self.state != self.state.upper():
            raise ValidationError({"state": "State must be uppercase."})

    def clean_zip(self):
        if self.zip.startswith("0"):
            raise ValidationError("Zip cannot start with 0.")


class Business(db.Model):

    id = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()
    employees = db.IntegerField(default=5, nullable=False)

    location = db.CompositeField(Address)
    other_location = db.CompositeField(Address, prefix="foo")

    def clean(self):
        if self.other_location and not self.location:
            raise ValidationError({"location": "Primary key is required when other location is provided."})


class Owner(db.Model):
    query_class = OwnerQuery

    id = db.IntegerField(autoincrement=True, primary_key=True)
    first_name = db.CharField()
    last_name = db.CharField()


class Vehicle(db.Model):
    id = db.IntegerField(autoincrement=True, primary_key=True, doc="The primary key")
    name = db.CharField(doc="The name of the vehicle")
    type = db.EnumField(choices=VehicleType, constraint_name="ck_vehicle_type", nullable=False)
    created_at = db.DateTimeField()
    paint = db.EnumField(choices=COLORS, constraint_name="ck_colors")
    is_used = db.BooleanField()

    owner = db.ManyToOne(Owner, backref="vehicles")

    @property
    def lower_name(self):
        return self.name.lower()

    @db.validates("name")
    def validate_name(self, key, value):
        if value == "Bad Vehicle":
            raise ValidationError("Name cannot be `Bad Value`")

        return value

    def clean_paint(self):
        if self.paint == "pink":
            raise ValidationError("Can't have a pink car")


class Part(db.Model):
    id = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()

    vehicles = db.ManyToMany(Vehicle, backref="parts", table_name="vehicle_parts")


class Option(db.Model):
    id = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()

    vehicles = db.ManyToMany(Vehicle, backref=db.backref("options"), table_name="vehicle_options")


class CompositePkModel(db.Model):
    query_class = None

    id = db.IntegerField(primary_key=True)
    pk = db.IntegerField(primary_key=True)
    name = db.CharField()

    is_active = db.BooleanField()

    active = db.queryproperty(is_active=True)


class DummyEnum(Enum):
    zero = 0
    one = 1
    two = 2


Choices = ["three", "four"]


@autocoerce
class AllKindsOfFields(db.Model):

    pk = db.Column(db.Integer(), primary_key=True)

    # flags
    boolean_notnull = db.Column(db.Boolean(), nullable=False)
    boolean = db.Column(db.Boolean())
    enum = db.Column(db.Enum(DummyEnum, name="dummy_enum"))
    enum_choice = db.Column(db.Enum(*Choices, name="some_choices"))

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
    # clob = db.Column(db.CLOB())
    nchar = db.Column(db.NCHAR())
    # nvarchar = db.Column(db.NVARCHAR())
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
    # blob = db.Column(db.BLOB())
    largebinary = db.Column(db.LargeBinary())
    # varbinary = db.Column(db.VARBINARY())


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

    pk = db.IntegerField(autoincrement=True, primary_key=True)

    x1 = db.IntegerField()
    y1 = db.IntegerField()
    x2 = db.IntegerField()
    y2 = db.IntegerField()

    start = db.composite(Point, x1, y1)
    end = db.composite(Point, x2, y2)


class ModelTwo(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()


class ModelOne(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()

    _model_twos = db.OneToMany(ModelTwo, backref="_model_one")


model_three_ones = db.Table(
    "model_three_ones",
    db.Column("model_one_pk", db.Integer(), db.ForeignKey("model_one.pk"), primary_key=True),
    db.Column("model_two_pk", db.Integer(), db.ForeignKey("model_three.pk"), primary_key=True),
)


class ModelThree(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String())

    model_ones = db.ManyToMany(ModelOne, secondary=model_three_ones)


class ModelFour(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()

    _model_twos = db.OneToMany(ModelTwo, backref=db.backref("_model_four"))


class ModelFullCleanFail(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()

    def clean(self):
        raise ValidationError("bad model")


class ValidateUniqueModel(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    name = db.CharField()
    foo = db.CharField()
    bar = db.CharField()

    validators = [ValidateUnique(db, "name"), ValidateUnique(db, "foo", "bar")]


class ClassicModel(object):
    pass


class SelectedAutoCoerce(db.Model):
    pk = db.IntegerField(autoincrement=True, primary_key=True)
    foo = db.DecimalField()
    bar = db.FloatField()
    me = db.IntegerField()


autocoerce_properties(SelectedAutoCoerce.foo, SelectedAutoCoerce.bar)


classic_model_table = db.Table(
    "classic_model", db.Column("pk", db.Integer(), autoincrement=True, primary_key=True), db.Column("name", db.String())
)
db.mapper(ClassicModel, classic_model_table)


db.configure_mappers()
db.drop_all()
db.create_all()
