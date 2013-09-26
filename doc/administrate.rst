Administrate
============

Users
-----

Nuancier-lite has basically two levels for the users:

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

Nuancier-lite will be able to find the pictures there.

However, to give a name to the candidate, nuancier-lite expects to find in
each folder a file: ``infos.txt`` containing, tab delimited, for each picture
its file name, author and name.

An example of infos.txt would be:

::

    filename1    author name1     image name 1
    filename2    author name2     image name 2
    filename3    author name3     image name 3
    ...


The character delimiting ``filename1`` from ``author name1`` and ``author name1``
from ``image name 1`` must be a **tabulation** (\t, <tab>).

.. note:: nuancier-lite will only consider the candidate present in the
   ``infos.txt`` file.


.. administration_panel:

Administration panel
---------------------

After logging in, if you are in the administrator group, you will see an
``Admin`` entry in the menu.

If you click on this ``Admin`` link you will arrive to the index page of the
administration panel.

This page shows you all elections registered with their information and for
each if they are open for vote or not and if their results are public or not.
It offers the possibility to (re-)generate the cache for an election and
get some statistics about it :
- Number of participants
- Number of votes,
- Maximum number of vote per person
- Average vote per person
- Bar graph indicating how many people voted on how many candidates, for
    example: 3 person voted to 4 candidates while 10 voted only on 2
    candidates.


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
simply log in nuancier-lite, go to the administration panel, find the
correct election and on the `Open` column click on the ``toggle`` link.

If fedmsg is installed on the server, fedmsg messages are published for these
events.


.. _publish_results:

Publish results of an election
-------------------------------

Once an election has ended, to publish its results, the administrator can
simply log in nuancier-lite, go to the administration panel, find the
correct election and on the `Published` column click on the ``toggle`` link.

If fedmsg is installed on the server, fedmsg messages are published for these
events.


.. _generate_cache:

Generate cache
--------------

To decrease the weight of the page where all the candidates of an election
are shown, nuancier-lite generates thumbnails.

To generate the cache of an election, the administrator needs to log in
nuancier-lite, go to the administration panel, find the correct election
and click on the ``(Re-)generate cache``.


.. note:: Nuancier-lite relies on the ``infos.txt`` (see
   :doc:`upload_candidates` for more information) to import the files as
   candidate in the database and will only generate the thumbnails of these
   files.
