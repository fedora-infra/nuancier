# -*- coding: utf-8 -*-
#
# Copyright © 2019  Red Hat, Inc. and others.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
#
"""Message schema for Elections."""

from fedora_messaging import message

from .common_schemas import election_schema


class ElectionCreated(message.Message):
    """
    Message sent by nuancier when a election is created.
    """

    topic = "nuancier.election.new"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a election is created in Nuancier",
        "type": "object",
        "required": ["agent", "election"],
        "properties": {
            "agent": {"type": "string"},
            "election": election_schema,
        },
    }

    def __str__(self):
        """
        Return a human-readable representation of this message.

        This should provide a detailed representation of the message, much like the body
        of an email.

        Returns:
            A human readable representation of this message.
        """
        return self.summary

    @property
    def summary(self):
        """
        Return a short, human-readable representation of this message.

        This should provide a short summary of the message, much like the subject line
        of an email.

        Returns:
            A summary for this message.
        """
        return "The election '{}' hes been created.".format(self.name)

    @property
    def name(self):
        """Returns the name of the election that was created."""
        return self.body['election']['name']


class ElectionEdited(message.Message):
    """
    Message sent by nuancier when a election is updated.
    """

    topic = "nuancier.election.update"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a election is updated in Nuancier",
        "type": "object",
        "required": ["agent", "election", "updated"],
        "properties": {
            "agent": {"type": "string"},
            "election": election_schema,
            "updated": {"type": "array"},
        },
    }

    def __str__(self):
        """
        Return a human-readable representation of this message.

        This should provide a detailed representation of the message, much like the body
        of an email.

        Returns:
            A human readable representation of this message.
        """
        return self.summary

    @property
    def summary(self):
        """
        Return a short, human-readable representation of this message.

        This should provide a short summary of the message, much like the subject line
        of an email.

        Returns:
            A summary for this message.
        """
        return "The election '{}' hes been created.".format(self.name)

    @property
    def name(self):
        """Returns the name of the election that was edited."""
        return self.body['election']['name']
