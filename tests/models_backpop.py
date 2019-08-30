# -*- coding: utf-8 -*-

from django_sorcery.db import databases


db = databases.get("minimal_backpop")


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
    profile = db.relationship("Profile", back_populates="customer", uselist=False)


class Profile(db.Model):
    pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
    name = db.Column(db.String(length=20))

    customer = db.OneToOne("Customer", back_populates="profile")


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
