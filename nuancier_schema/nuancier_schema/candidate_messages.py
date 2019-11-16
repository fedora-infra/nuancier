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
"""Message schema for Candidates."""

from fedora_messaging import message

from .common_schemas import election_schema, candidate_schema


class CandidateApproved(message.Message):
    """
    Message sent by nuancier when a candidate is approved.
    """

    topic = "nuancier.candidate.approved"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a candidate is approved in Nuancier",
        "type": "object",
        "required": ["agent", "election", "candidate"],
        "properties": {
            "agent": {"type": "string"},
            "election": election_schema,
            "candidate": candidate_schema,
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
        return "The candidate '{}' hes been approved.".format(self.name)

    @property
    def name(self):
        """Returns the name of the candidate that was approved."""
        return self.body['candidate']['name']


class CandidateDenied(message.Message):
    """
    Message sent by nuancier when a candidate is denied.
    """

    topic = "nuancier.candidate.denied"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a candidate is denied in Nuancier",
        "type": "object",
        "required": ["agent", "election", "candidate"],
        "properties": {
            "agent": {"type": "string"},
            "election": election_schema,
            "candidate": candidate_schema,
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
        return "The candidate '{}' hes been denied.".format(self.name)

    @property
    def name(self):
        """Returns the name of the candidate that was denied."""
        return self.body['candidate']['name']


class CandidateCreated(message.Message):
    """
    Message sent by nuancier when a candidate is created.
    """

    topic = "nuancier.candidate.new"
    body_schema = {
        "id": "https://fedoraproject.org/jsonschema/anitya_distro_editedv1.json",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent when a candidate is created in Nuancier",
        "type": "object",
        "required": ["agent", "election", "candidate"],
        "properties": {
            "agent": {"type": "string"},
            "election": election_schema,
            "candidate": candidate_schema,
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
        return "The candidate '{}' hes been created.".format(self.name)

    @property
    def name(self):
        """Returns the name of the candidate that was created."""
        return self.body['candidate']['name']
