nuancier
========

:Author: Pierre-Yves Chibon <pingou@pingoured.fr>


Nuancier is a web-based voting application for the supplementary
wallpapers of Fedora.


Get this project:
-----------------
On github: https://github.com/fedora-infra/nuancier

Documentation: http://nuancier.rtfd.org


Dependencies:
-------------
.. _python: http://www.python.org
.. _Flask: http://flask.pocoo.org/
.. _python-flask: http://flask.pocoo.org/
.. _python-flask-wtf: http://packages.python.org/Flask-WTF/
.. _python-wtforms: http://wtforms.simplecodes.com/docs/1.0.1/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _python-sqlalchemy: http://www.sqlalchemy.org/
.. _Pillow: https://pypi.python.org/pypi/Pillow
.. _python-pillow: https://pypi.python.org/pypi/Pillow
.. _dogpile.cache: https://pypi.python.org/pypi/dogpile.cache

This project is a `Flask`_ application. The calendars and meetings are
stored into a relational database using `SQLAlchemy`_ as Object Relational
Mapper (ORM).
The application relies on `Pillow`_ to generate thumbnails of the pictures in
order to increase the loading speed of the pages.


The dependency list is therefore:

- `python`_ (3.7 minimum)
- `python-flask`_
- `python-flask-wtf`_
- `python-wtforms`_
- `python-sqlalchemy`_
- `python-pillow`_
- `dogpile.cache`_


Running a development instance:
-------------------------------

You can either set up a development environment manually, or using Ansible
with Vagrant.

Vagrant
^^^^^^^

The best way to set up a development enviroment is to use `Vagrant <https://vagrantup.com/>`_.
Vagrant provisions a new virtual machine and then runs the Ansible playbook on it automatically.
To get started, install Vagrant::

    $ sudo dnf install vagrant libvirt vagrant-libvirt vagrant-sshfs ansible git

Next, clone the repository and copy the example Vagrantfile from ``Vagrantfile.example``::

    $ git clone https://github.com/fedora-infra/nuancier.git
    $ cd nuancier
    $ cp Vagrantfile.example Vagrantfile  # Edit Vagrantfile to your heart's content
    $ vagrant up
    $ vagrant reload
    $ vagrant ssh

All done! The VM contains all the required dependencies pre-installed.


Manual
^^^^^^

Instructions here have been tested on Fedora 30, using Python3

Get git and python3:

    sudo dnf install git python3

Clone the source::

    git clone https://github.com/fedora-infra/nuancier.git

Install Python requirements

    pip3 install -r requirements.txt
 
Create the database scheme::

    python3 createdb.py

Run the server locally::

    python3 runserver.py

You should be able to access the server at http://localhost:5000

or to run the server externally, first open relevant port in firewall::

    sudo firewall-cmd --add-port 5000/tcp --permanent
    sudo firewall-cmd --reload 
 
then run the server::

    python3 runserver.py --host 0.0.0.0

You should be able to access the server at http://ip.address:5000

.. note:: To tweak the configuration, you may either change
   ``default_config.py`` in the nuancier module, or copy the file
   ``utility/nuancier.cfg.sample`` into ``nuancier.cfg`` and run the
   application using::

     NUANCIER_CONFIG=nuancier.cfg python runserver.py

Testing:
--------

This project contains unit-tests allowing you to check if your server
has all the dependencies correctly set.

To run them::

 ./runtests.sh

.. note:: To stop the test at the first error or failure you can try:

   ::

    ./runtests.sh -x


License:
--------

This project is licensed GPLv2+.
