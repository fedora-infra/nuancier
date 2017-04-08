# -*- coding: utf-8 -*-
#
# Copyright © 2016-2017  Red Hat, Inc.
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
"""
Unit tests for :module:`nuancier.forms`
"""
from __future__ import unicode_literals, absolute_import

import datetime
import unittest

import mock

from nuancier import forms, APP


try:
    import flask_wtf
    flask_wtf.__version__
    VERY_OLD_VERSION = False
except AttributeError:
    VERY_OLD_VERSION = True


@mock.patch('nuancier.forms.flask_wtf.Form.__init__', new=mock.Mock())
class BaseFormTests(unittest.TestCase):
    """
    Tests for the BaseForm class. These are horrifying because internal APIs
    changed between flask-wtf-0.8 and the current version. This is why the
    actual __init__ method is mocked out, since one version requires TIME_LIMIT
    to be an integer, and the other a timedelta object.
    """

    def test_no_version_attr(self):
        """Assert that an AttributeError getting __version__ is handled"""
        with APP.test_request_context('/'):
            with mock.patch('nuancier.forms.flask_wtf'):
                # Demonstrate we get an AttributeError for __version__
                self.assertRaises(AttributeError, getattr, forms.flask_wtf, '__version__')
                form = forms.BaseForm()
                self.assertEqual(
                    datetime.timedelta(seconds=3600), form.TIME_LIMIT)

    @unittest.skipIf(VERY_OLD_VERSION, "flask-wtf is too old to run this test")
    def test_old_version_using_new(self):
        """Assert that for old versions, TIME_LIMIT is set on forms"""
        with APP.test_request_context('/'):
            for v in ('0.8', '0.9'):
                with mock.patch('nuancier.forms.flask_wtf.__version__', new=v):
                    form = forms.BaseForm()
                    self.assertEqual(
                        datetime.timedelta(seconds=3600), form.TIME_LIMIT)

    @unittest.skipIf(not VERY_OLD_VERSION, "flask-wtf is too new to run this test")
    def test_old_version_using_old(self):
        """Assert that for old versions, TIME_LIMIT is set on forms"""
        with APP.test_request_context('/'):
            form = forms.BaseForm()
            self.assertEqual(
                datetime.timedelta(seconds=3600), form.TIME_LIMIT)

    @unittest.skipIf(VERY_OLD_VERSION, "flask-wtf is too old to run this test")
    def test_new_version_using_new(self):
        """Assert that for new versions, TIME_LIMIT isn't set on forms"""
        with APP.test_request_context('/'):
            for v in ('1.0.0', '0.10.1', '2.13.0'):
                with mock.patch('nuancier.forms.flask_wtf.__version__', new=v):
                    form = forms.BaseForm()
                    self.assertIs(None, form.TIME_LIMIT)


if __name__ == '__main__':
    unittest.main()
