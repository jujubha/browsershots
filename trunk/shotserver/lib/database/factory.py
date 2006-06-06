# -*- coding: utf-8 -*-
# browsershots.org
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Database interface for factory table.
"""

__revision__ = '$Rev$'
__date__ = '$Date$'
__author__ = '$Author$'

def select_serial(name):
    """
    Get the serial number from the database.
    """
    cur.execute("SELECT factory FROM factory WHERE name=%s", (name, ))
    result = cur.fetchone()
    if result is not None:
        return result[0]
    raise KeyError("factory.name=%s" % name)

def select_salt(factory):
    """
    Get the password salt for a factory.
    If there's no factory password, get the factory owner's salt.
    """
    sql = []
    sql.append("SELECT factory.salt, owner.salt")
    sql.append("FROM factory")
    sql.append("JOIN person AS owner ON factory.owner = owner.person")
    sql.append("WHERE factory = %s")
    cur.execute(' '.join(sql), (factory, ))
    factory_salt, owner_salt = cur.fetchone()
    if factory_salt is None:
        return owner_salt
    return factory_salt
