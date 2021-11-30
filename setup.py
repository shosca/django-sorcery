#!/usr/bin/env python
# fmt:off
import os

from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))


about = {}
with open(os.path.join(here, "django_sorcery", "__version__.py")) as f:
    exec(f.read(), about)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), "rb").read().decode("utf-8")


setup(
    author=about["__author__"],
    author_email=about["__author_email__"],
    description=about["__description__"],
    include_package_data=True,
    install_requires=["alembic", "blinker", "inflect", "django", "python-dateutil", "sqlalchemy<2"],
    license="MIT",
    long_description=read("README.rst"),
    name="django-sorcery",
    packages=find_packages(exclude=["tests", "tests.*"]),
    entry_points={"pytest11": ["django-sorcery = django_sorcery.pytest_plugin"]},
    url="https://github.com/shosca/django-sorcery",
    version=about["__version__"],
    keywords="sqlalchemy django framework forms",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    project_urls={
        "Documentation": "https://django-sorcery.readthedocs.io",
        "Source": "https://github.com/shosca/django-sorcery",
    },
)
