Django Sorcery
==============

|Build Status| |Read The Docs| |PyPI version| |Coveralls Status|

* Free software: MIT license
* GitHub: https://github.com/shosca/django-sorcery

**Django Framework integration with SQLAlchemy**

SQLAlchemy is an excellent orm. And Django is a great framework, until you decide not to use Django ORM. This library
provides utilities, helpers and configurations to ease the pain of using SQLAlchemy with Django. It aims to provide
a similar development experience to building a Django application with Django ORM, except with SQLAlchemy.

Installation
============

::

    pip install django-sorcery

Quick Start
===========

Lets start by creating a site:

.. code:: console

    $ django-admin startproject mysite

And lets create an app:

.. code:: console

    $ cd mysite
    $ python manage.py startapp polls

This will create a polls app with standard django app layout:

.. code:: console

    $ tree
    .
    ├── manage.py
    ├── polls
    │   ├── admin.py
    │   ├── apps.py
    │   ├── __init__.py
    │   ├── migrations
    │   │   └── __init__.py
    │   ├── models.py
    │   ├── tests.py
    │   └── views.py
    └── mysite
        ├── __init__.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py

    3 directories, 12 files

And lets add our ``polls`` app in ``INSTALLED_APPS`` in ``mysite/settings.py``:

.. code:: python

    INSTALLED_APPS = [
        'polls.apps.PollsConfig',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
    ]

Now we're going to make a twist and start building our app with ``sqlalchemy``. Lets define our models in
``polls/models.py``:

.. code:: python

    from django_sorcery.db import databases


    db = databases.get("default")


    class Question(db.Model):
        pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
        question_text = db.Column(db.String(length=200))
        pub_date = db.Column(db.DateTime())


    class Choice(db.Model):
        pk = db.Column(db.Integer(), autoincrement=True, primary_key=True)
        choice_text = db.Column(db.String(length=200))
        votes = db.Column(db.Integer())


    db.configure_mappers()
    db.create_all()

Right now, we have enough to hop in django shell:

.. code:: console

    $ python manage.py shell

    >>> from polls.models import Choice, Question, db  # Import the model classes and the db

    # we have no choices or questions in db yet
    >>> Choice.query.all()
    []
    >>> Question.query.all()
    []

    # Lets create a new question
    >>> from django.utils import timezone
    >>> q = Question(question_text="What's new?", pub_date=timezone.now())
    >>> q
    Question(pk=None, pub_date=datetime.datetime(2018, 5, 19, 0, 54, 20, 778186, tzinfo=<UTC>), question_text="What's new?")

    # lets save our question, we need to add our question to the db
    >>> db.add(q)

    # at this point the question is in pending state
    >>> db.new
    IdentitySet([Question(pk=None, pub_date=datetime.datetime(2018, 5, 19, 0, 54, 20, 778186, tzinfo=<UTC>), question_text="What's new?")])

    # lets flush to the database
    >>> db.flush()

    # at this point our question is in persistent state and will receive a primary key
    >>> q.pk
    1

    # lets change the question text
    >>> q.question_text = "What's up?"
    >>> db.flush()

    # Question.objects and Question.query are both query properties that return a query object bound to db
    >>> Question.objects
    <django_sorcery.db.query.Query at 0x7feb1c7899e8>
    >>> Question.query
    <django_sorcery.db.query.Query at 0x7feb1c9377f0>

    # and lets see all the questions
    >>> Question.objects.all()
    [Question(pk=1, pub_date=datetime.datetime(2018, 5, 19, 0, 54, 20, 778186, tzinfo=<UTC>), question_text="What's up?")]


.. |Build Status| image:: https://travis-ci.org/shosca/django-sorcery.svg?branch=master
   :target: https://travis-ci.org/shosca/django-sorcery
.. |Read The Docs| image:: https://readthedocs.org/projects/django-sorcery/badge/?version=latest
   :target: http://django-sorcery.readthedocs.io/en/latest/?badge=latest
.. |PyPI version| image:: https://badge.fury.io/py/django-sorcery.svg
   :target: https://badge.fury.io/py/django-sorcery
.. |Coveralls Status| image:: https://coveralls.io/repos/github/shosca/django-sorcery/badge.svg?branch=master
   :target: https://coveralls.io/github/shosca/django-sorcery?branch=master
