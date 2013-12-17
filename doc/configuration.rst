Configuration
=============

There are the main configuration options to set to have nuancier
running.
These options are all present and described in the nuancier.cfg file.

The secret key
---------------

Set in the configuration file under the key ``SECRET_KEY``, this is a unique,
random string which is used by `Flask <http://flask.pocoo.org>`_ to generate
the `CSRF <http://en.wikipedia.org/CSRF>`_ key unique for each user.


You can easily generate one using `pwgen <http://sf.net/projects/pwgen>`_
for example to generate a 50 characters long random key
::

  pwgen 50


The database URL
-----------------

Nuancier uses `SQLAlchemy <http://sqlalchemy.org>`_ has Object
Relationship Mapper and thus to connect to the database. You need to provide
under the key ``DB_URL`` in the configuration file the required information
to connect to the database.


Examples URLs are::

  DB_URL=mysql://user:pass@host/db_name
  DB_URL=postgres://user:pass@host/db_name
  DB_URL=sqlite:////full/path/to/database.sqlite


.. note:: The key ``sqlalchemy.url`` of the ``alembic.ini`` file should
          have the same value as the ``DB_URL`` described here.


The admin group
----------------

Nuancier relies on a group of administrator to create new elections,
open or close them for voting and open or close the publication of the
results and (re)generate the cache.
The ``ADMIN_GROUP`` field in the configuration file refers to the
`FAS <https://admin.fedoraproject.org/accounts>`_ group that manages this
nuancier instance.

See :doc:`usage` for details explanations on the different administration
layer of nuancier.

.. note:: Several groups of administrators can be set using either () or [].


The pictures folder
-------------------

The ``PICTURE_FOLDER`` field provides to the application the full path
to the folder in which are placed the pictures candidates for the elections
(within a folder, specific for each election).


The cache folder
-------------------

The ``CACHE_FOLDER`` field provides to the application the full path
to the folder in which the application is allowed to generate the thumbnails
of the pictures present in the ``PICTURE_FOLDER``.

.. note:: This folder should be writtable by the application (ie: apache).


The thumb size
---------------

In order to decrease the weight of the pages displaying all the pictures
candidate to an election, nuancier creates thumbnails of these pictures.
These thumbnails are generated with anti-aliases to maintain a certain quality.

The ``THUMB_SIZE`` is a set of length, width coordinate providing indication
to nuancier about the desired size of the thumbnails.

By default ``THUMB_SIZE`` is at 256x256.
