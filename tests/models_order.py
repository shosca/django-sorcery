# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import SQLAlchemy


db = db = SQLAlchemy("minimal")


class Asset(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))


class OrderItem(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))


class Customer(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))


class Contact(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))


class Order(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    order_item = db.ManyToOne(OrderItem, backref=db.backref("orders"), fk_name="fk_order_order_item")

    applicant = db.ManyToOne(Customer, backref=db.backref("orders"), fk_name="fk_order_applicant")

    coapplicant = db.ManyToOne(Customer, backref=db.backref("other_orders"), fk_name="fk_order_coapplicant")

    assets = db.OneToMany(Asset, backref="order", fk_name="fk_order_assets")

    contacts = db.ManyToMany(Contact, backref="orders", table_name="order_contacts")


db.configure_mappers()
db.drop_all()
db.create_all()
