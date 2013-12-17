Development
===========

Get the sources
---------------

Anonymous:

::

  git clone https://github.com/fedora-infra/nuancier.git

Contributors:

::

  git clone git@github.com:fedora-infra/nuancier.git


Dependencies
------------

The dependencies of nuancier are listed in the file ``requirements.txt``
at the top level of the sources.


Run nuancier for development
---------------------------------
Create the database scheme::

  python createdb.py

Run the server::

  ./runserver

You should be able to access the server at http://localhost:5000


Every time you save a file, the project will be automatically restarted
so you can see your change immediatly.

.. note:: You may want to adjust the values in ``nuancier/default_config.py``
   especially the ``ADMIN_GROUP`` if you are not part of the default one.
   See :doc:`configuration` for more information about the configuration.


Coding standards
----------------

We are trying to make the code `PEP8-compliant
<http://www.python.org/dev/peps/pep-0008/>`_.  There is a `pep8 tool
<http://pypi.python.org/pypi/pep8>`_ that can automatically check
your source.


We are also inspecting the code using `pylint
<http://pypi.python.org/pypi/pylint>`_ and aim of course for a 10/10 code
(but it is an assymptotic goal).

.. note:: both pep8 and pylint are available in Fedora via yum:

          ::

            yum install python-pep8 pylint


Send patch
----------

The easiest way to work on nuancier is to make your own branch in git,
make your changes to this branch, commit whenever you want, rebase on master,
whenever you need and when you are done, send the patch either by email or
via the github pull-request mechanism.


The workflow would therefore be something like:

::

   git branch <my_shiny_feature>
   git checkout <my_shiny_feature>
   <work>
   git commit file1 file2
   <more work>
   git commit file3 file4
   git checkout master
   git pull
   git checkout <my_shiny_feature>
   git rebase master
   git format-patch -2

This will create two patch files that you can send by email to submit in the
trac.


Unit-tests
----------

Nuancier has a number of unit-tests providing at the moment a full
coverage of the backend library (nuancier.lib).


We aim at having a full (100%) coverage of the whole code (including the Flask
application) and of course a smart coverage as in we want to check that the
functions work the way we want but also that they fail when we expect it and
the way we expect it.


Tests checking that function are failing when/how we want are as important
as tests checking they work the way they are intended to.


``runtests.sh``, located at the top of the sources, helps to run the
unit-tests of the project with coverage information using `python-nose
<https://nose.readthedocs.org/>`_.


.. note:: You can specify additional arguments to the nose command used
          in this script by just passing arguments to the script.
          
          For example you can specify the ``-x`` / ``--stop`` argument:
          `Stop running tests after the first error or failure` by just doing

          ::

            ./runtests.sh --stop


Each unit-tests files (located under ``tests/``) can be called
by alone, allowing easier debugging of the tests. For example:

::

  python tests/test_model.py

Similarly as for nose you can also ask that the unit-test stop at the first
error or failure. For example, the command could be:

::

  python -m unittest -f -v tests.test_model


.. note:: In order to have coverage information you might have to install
          ``python-coverage``

          ::

            yum install python-coverage


Database changes
----------------

We try to make the database schema as stable as possible, however once in a
while we need to change it to add new features or information.


When database changes are made, they should have the corresponding change
handled via `alembic <http://pypi.python.org/pypi/alembic>`_.


See the `alembic tutorial
<http://alembic.readthedocs.org/en/latest/tutorial.html>`_ for complete
information on how to make a revision to the database schema.


The basic idea is to create a revision using (in the top folder):

::

  alembic revision -m "<description of the change>"

Then edit the file generated in alembic/versions/ to add the correct command
for upgrade and downgrade (for example: ``op.add_column``, ``op.drop_column``,
``op.create_table``, ``op.drop_table``).
