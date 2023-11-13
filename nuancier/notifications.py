# -*- coding: utf-8 -*-
#
# Copyright © 2013-2019  Red Hat, Inc. and others.
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
notification shim for nuancier
'''

import smtplib
import warnings

from email.mime.text import MIMEText
from fedora_messaging import api as fm_api
from fedora_messaging.exceptions import PublishReturned, ConnectionException

import nuancier


## Let's ignore the warning about a global variable being in lower case
# pylint: disable=C0103


def publish(msg):  # pragma: no cover
    ''' Send a message via Fedora Messaging. '''
    try:
        fm_api.publish(msg)
    except PublishReturned as e:
        nuancier.LOG.exception(
            'Fedora Messaging broker rejected message %s: %s',
            message.id, e)
    except ConnectionException as e:
        nuancier.LOG.exception('Error sending message %s: %s', message.id, e)


def email_publish(to_email, img_title, motif):  # pragma: no cover
    ''' Send notification by email. '''

    message = """
Dear Madam/Sir,

First of all we would like to thank you for contributing in making Fedora
better by submitting a supplementary wallpaper in Nuancier.

However, we regrets to inform you that your contribution has been rejected
by the administrator for the following reason:

  {0}

This should not discourage you to submit other candidate for this election
or the next one.

Best regards,
The Nuancier administrators team
""".format(motif)

    msg = MIMEText(message)
    msg['Subject'] = '[Nuancier] {0} has been rejected'.format(
        img_title.encode('utf-8'))
    from_email = nuancier.APP.config.get(
        'NUANCIER_EMAIL_FROM', 'nobody@fedoraproject.org')
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(nuancier.APP.config.get(
        'NUANCIER_EMAIL_SMTP_SERVER', 'localhost'))
    smtp.sendmail(from_email, [to_email], msg.as_string())
    smtp.quit()
