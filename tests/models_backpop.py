# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django_sorcery.db import SQLAlchemy


db = db = SQLAlchemy("minimal_backpop")


class Asset(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    order = db.ManyToOne("Order", back_populates="assets")


class OrderItem(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    orders = db.OneToMany("Order", back_populates="order_item")


class Customer(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    orders = db.OneToMany("Order", back_populates="applicant")
    coapp_orders = db.OneToMany("Order", back_populates="coapplicant")


class Contact(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    orders = db.ManyToMany("Order", back_populates="contacts", table_name="order_contacts")


class Order(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=5))

    order_item = db.ManyToOne("OrderItem", back_populates="orders")

    applicant = db.ManyToOne("Customer", back_populates="orders")

    coapplicant = db.ManyToOne("Customer", back_populates="coapp_orders")

    assets = db.OneToMany(Asset, back_populates="order")

    contacts = db.ManyToMany("Contact", back_populates="orders", table_name="order_contacts")


db.configure_mappers()
db.drop_all()
db.create_all()
