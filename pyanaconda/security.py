#
# security.py - security install data and installation
#
# Copyright (C) 2004  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Jeremy Katz <katzj@redhat.com>
#

import iutil
from flags import flags
from pyanaconda.constants import ROOT_PATH
from pykickstart.constants import *

import logging
log = logging.getLogger("anaconda")

selinux_states = { SELINUX_DISABLED: "disabled",
                   SELINUX_ENFORCING: "enforcing",
                   SELINUX_PERMISSIVE: "permissive" }

class Security:
    def __init__(self):
        if flags.selinux == 1:
            self.selinux = SELINUX_ENFORCING
        else:
            self.selinux = SELINUX_DISABLED

    def setSELinux(self, val):
        if not selinux_states.has_key(val):
            log.error("Tried to set to invalid SELinux state: %s" %(val,))
            val = SELINUX_DISABLED

        self.selinux = val

    def getSELinux(self):
        return self.selinux

    def write(self):
        args = []

        if not selinux_states.has_key(self.selinux):
            log.error("unknown selinux state: %s" %(self.selinux,))
            return

        try:
            iutil.execWithRedirect("/usr/sbin/lokkit", args,
                                   root=ROOT_PATH, stdout="/dev/null",
                                   stderr="/dev/null")
        except (RuntimeError, OSError) as msg:
            log.error ("lokkit run failed: %s" %(msg,))