Administrate
============

Users
-----

Nuancier has basically two levels for the users:

 - administrators
 - users


Administrators
~~~~~~~~~~~~~~

Administrators are people with an account on the
`Fedora account system (FAS) <https://admin.fedoraproject.org/accounts/>`_
and belong the one of administrator groups as set in the :doc:`configuration`.

Administrators are the only people allowed to create an election, open or
close it for votes, open or close the results and generate the cache
(thumbnails).


Users
~~~~~

Users are people with an account on the
`Fedora account system (FAS) <https://admin.fedoraproject.org/accounts/>`_ and
belong to at least one more group than the ``fedora_cla`` group which
every contributor should sign to contribute to Fedora.


.. upload_candidates:

Upload new pictures for an election
-----------------------------------

When preparing an election, the election wrangler needs to gather all the
candidate wallpapers into a folder, with a unique name and place this folder
in the directory specified under ``PICTURE_FOLDER`` in :doc:`configuration`.



.. administration_panel:

Administration panel
---------------------

After logging in, if you are in the administrator group, you will see an
``Admin`` entry in the menu.

If you click on this ``Admin`` link you will arrive to the index page of the
administration panel.

This page shows you all elections registered with their information and for
each if they are open for vote or not and if their results are public or not.
It offers the possibility to (re-)generate the cache for an election and once
the election is closed, a link to some statistics about it.


.. _create_elections:

Create elections
----------------

Click on the link ``Create a new election`` from the administration panel.

The form to will ask for:

- ``election name``: the name of the election, this will be used as link
  throughout the application.
  Example name might be : `Fedora 20 wallpaper`

- ``Name of the folder containing the pictures``: this specifies the name
  of the folder containing the pictures for that election that has been
  placed in the folder specified under ``PICTURE_FOLDER`` in
  :doc:`configuration`.
  .. note:: It is a good idea to keep this name simple, unique, ascii and
     and without spaces.

- ``Year``: the year the election is taking place, this is purely for
  information.

- ``Open``: This is a checkbox to specify whether this election is already
  open for votes or not.

- ``URL to claim a badge for voting``: this allows to specify a link where
  people will be able to go to collect a badge announcing they participated
  on this election. You should coordinate with the people of the
  `badge <https://fedorahosted.org/fedora-badges/>`_ project to get this
  link.

- ``Number of votes a user can make``: this specifies the number of choices
  a user can make for this election.
  For example, a user might be allowed to select only 16 wallpapers, thus
  this field should be `16`.

- ``Generate cache``: this is checkbox offering to generate the cache
  assuming the pictures have already been placed on the ``PICTURE_FOLDER``,
  together with the ``infos.txt`` file.


.. _open_close_election:

Open/Close election for votes
------------------------------

Once an election is opened for vote or has ended, the administrator can
simply log in nuancier, go to the administration panel, find the
correct election and on the `Open` column click on the ``toggle`` link.

If fedmsg is installed on the server, fedmsg messages are published for these
events.


.. _publish_results:

Publish results of an election
-------------------------------

Once an election has ended, to publish its results, the administrator can
simply log in nuancier, go to the administration panel, find the
correct election and on the `Published` column click on the ``toggle`` link.

If fedmsg is installed on the server, fedmsg messages are published for these
events.


.. _generate_cache:

Generate cache
--------------

To decrease the weight of the page where all the candidates of an election
are shown, nuancier generates thumbnails.

To generate the cache of an election, the administrator needs to log in
nuancier, go to the administration panel, find the correct election
and click on the ``(Re-)generate cache``.

