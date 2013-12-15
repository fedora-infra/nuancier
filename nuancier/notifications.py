# -*- coding: utf-8 -*-
#
# Copyright © 2013  Red Hat, Inc.
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

'''
fedmsg shim for nuancier-lite
'''

## Let's ignore the warning about a global variable being in lower case
# pylint: disable=C0103
## Let's ignore the fact that pylint cannot import fedmsg
# pylint: disable=F0401


fedmsg = None
try:  # pragma: no cover
    import fedmsg
except ImportError:  # pragma: no cover
    pass


if fedmsg:
    fedmsg.init()


def publish(topic, msg):  # pragma: no cover
    ''' Send a message on the fedmsg bus. '''
    if not fedmsg:
        return

    fedmsg.publish(topic=topic, msg=msg)
