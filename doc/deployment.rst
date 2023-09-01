Deployment
==========

From sources
------------

Clone the source::

 git clone https://github.com/fedora-infra/nuancier.git
 cd nuancier


Copy the configuration files::

  cp utility/nuancier.cfg.sample nuancier.cfg

Adjust the configuration files (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   NUANCIER_CONFIG=/path/to/nuancier.cfg python createdb.py


Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install nuancier::

  dnf install nuancier

Adjust the configuration files: ``/etc/nuancier/nuancier.cfg``.
See :doc:`configuration` for detailed information about the configuration.

Create the database scheme::

   NUANCIER_CONFIG=/etc/nuancier/nuancier.cfg python /usr/share/nuancier/nuancier_createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  dnf install mod_wsgi


Then configure apache::

 sudo vim /etc/httpd/conf.d/nuancier.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/nuancier/nuancier.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/nuancier


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run nuancier just to test it.

