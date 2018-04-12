# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest

from ..models import CompositePkModel, Owner, db


class TestQuery(unittest.TestCase):

    def setUp(cls):
        super(TestQuery, cls).setUp()
        db.add_all(
            [
                Owner(id=1, first_name="Test 1", last_name="Owner 1"),
                Owner(id=2, first_name="Test 2", last_name="Owner 2"),
                Owner(id=3, first_name="Test 3", last_name="Owner 3"),
                Owner(id=4, first_name="Test 4", last_name="Owner 4"),
            ]
        )
        db.add(CompositePkModel(id=1, pk=1, active=True, name="Test-1-1"))
        db.flush()

    def tearDown(self):
        super(TestQuery, self).tearDown()
        db.rollback()
        db.remove()

    def test_query_get_regular(self):
        owner = Owner.query.get(1)
        self.assertEqual(owner.id, 1)

    def test_query_get_with_kwargs(self):
        owner = Owner.query.get(id=1)
        self.assertEqual(owner.id, 1)

    def test_query_get_with_kwargs_composite(self):
        obj = CompositePkModel.query.get(id=1, pk=1)
        self.assertEqual(obj.name, "Test-1-1")

    def test_query_get_with_kwargs_tuple(self):
        obj = CompositePkModel.query.get((1, 1))
        self.assertEqual(obj.name, "Test-1-1")
