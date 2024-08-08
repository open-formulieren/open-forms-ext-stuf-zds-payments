

Welcome to open-forms-ext-stuf-zds-payments's documentation!
=================================================

:Version: 0.1.0
:Source: https://github.com/open-formulieren/open-forms-ext-stuf-zds-payments
:Keywords: ``<keywords>``
:PythonVersion: 3.10, 3.12

|build-status| |code-quality| |black| |coverage| |docs|

|python-versions| |django-versions| |pypi-version|

Extra payment attributes for Open Forms StUF-ZDS registration backend

.. contents::

.. section-numbering::

Features
========

* Extra payment attributes for Open Forms StUF-ZDS registration backend

Installation
============

Requirements
------------

* Python 3.10/3.12 or above
* Django 4.2 or newer


Install
-------

.. code-block:: bash

    pip install open-forms-ext-stuf-zds-payments


Usage
=====

<document or refer to docs>

Local development
=================

To install and develop the library locally, use::

.. code-block:: bash

    pip install -e .[tests,coverage,docs,release]

When running management commands via ``django-admin``, make sure to add the root
directory to the python path (or use ``python -m django <command>``):

.. code-block:: bash

    export PYTHONPATH=. DJANGO_SETTINGS_MODULE=testapp.settings
    django-admin check
    # or other commands like:
    # django-admin makemessages -l nl


.. |build-status| image:: https://github.com/open-formulieren/open-forms-ext-stuf-zds-payments/workflows/Run%20CI/badge.svg
    :alt: Build status
    :target: https://github.com/open-formulieren/open-forms-ext-stuf-zds-payments/actions?query=workflow%3A%22Run+CI%22

.. |code-quality| image:: https://github.com/open-formulieren/open-forms-ext-stuf-zds-payments/workflows/Code%20quality%20checks/badge.svg
     :alt: Code quality checks
     :target: https://github.com/open-formulieren/open-forms-ext-stuf-zds-payments/actions?query=workflow%3A%22Code+quality+checks%22

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |coverage| image:: https://codecov.io/gh/open-formulieren/open-forms-ext-stuf-zds-payments/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/open-formulieren/open-forms-ext-stuf-zds-payments
    :alt: Coverage status

.. |docs| image:: https://readthedocs.org/projects/stuf_zds_payments/badge/?version=latest
    :target: https://stuf_zds_payments.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/open-forms-ext-stuf-zds-payments.svg

.. |django-versions| image:: https://img.shields.io/pypi/djversions/open-forms-ext-stuf-zds-payments.svg

.. |pypi-version| image:: https://img.shields.io/pypi/v/open-forms-ext-stuf-zds-payments.svg
    :target: https://pypi.org/project/open-forms-ext-stuf-zds-payments/
