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
"""Schema for common nuancier objects."""


election_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "year": {"type": "integer"},
        "date_start": {"type": "string"},
        "date_end": {"type": "string"},
        "submission_date_start": {"type": "string"},
        "submission_date_end": {"type": "string"},
    },
    "required": [
        "id",
        "name",
        "year",
        "date_start",
        "date_end",
        "submission_date_start",
        "submission_date_end",
    ],
}

candidate_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "author": {"type": "string"},
        "original": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "license": {"type": "string"},
        "submitter": {"type": "string"},
    },
    "required": [
        "name",
        "author",
        "license",
        "submitter",
    ],
}
