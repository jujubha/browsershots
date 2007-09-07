# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# Browsershots is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Browsershots is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
GUI-specific interface functions for X11.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"


import os
import shutil
from glob import glob
from shotfactory04.gui import linux as base


class Gui(base.Gui):
    """
    Special functions for IEs4Linux.
    """

    def reset_browser(self):
        """
        Delete browser cache.
        """
        dotdir = glob(os.path.join(os.environ['HOME'], '.ies4linux', '*',
            'drive_c', 'windows', 'profiles', '*', '*',
            'Temporary Internet Files'))
        for cachedir in dotdir:
            while os.path.islink(cachedir):
                cachedir = os.readlink(cachedir)
            if os.path.exists(cachedir):
                print 'deleting cache', cachedir
                shutil.rmtree(cachedir)