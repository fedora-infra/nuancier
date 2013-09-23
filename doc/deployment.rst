Deployment
==========

From sources
------------

Clone the source::

 git clone https://github.com/fedora-infra/nuancier-lite.git


Copy the configuration files::

  cp nuancier-lite.cfg.sample nuancier-lite.cfg

Adjust the configuration files (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   NUANCIER_CONFIG=/path/to/nuancier-lite.cfg python createdb.py


Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install nuancier-lite::

  yum install nuancier-lite

Adjust the configuration files: ``/etc/nuancier/nuancier-lite.cfg``.
See :doc:`configuration` for detailed information about the configuration.

Create the database scheme::

   NUANCIER_CONFIG=/etc/nuancier/nuancier-lite.cfg python /usr/share/nuancier/nuancier-lite_createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  yum install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/nuancier-lite.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/nuancier/nuancier-lite.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/nuancier


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run nuancier-lite just to test it.

