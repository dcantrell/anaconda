#
# Copyright (C) 2012  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Vratislav Podzimek <vpodzime@redhat.com>
#

"""
Module facilitating the work with NTP servers and NTP daemon's configuration

"""

import re, os, tempfile

NTP_CONFIG_FILE = "/etc/chrony.conf"

#example line:
#server 0.fedora.pool.ntp.org iburst
SRV_LINE_REGEXP = re.compile(r"^\s*server\s*([-a-zA-Z.0-9]+)\s*[a-zA-Z]+\s*$")

class NTPconfigError(Exception):
    """Exception class for NTP related problems"""
    pass

def ntp_server_working(server):
    """
    Runs rdate to try to connect to the $server (timeout may take some time).

    @return: True if the given server is reachable and working, False otherwise

    """

    #FIXME: It would be nice to use execWithRedirect here, but it is not
    #       thread-safe and hangs if this function is called from threads.
    #       By using tee (and block-buffered pipes) it is also much slower.
    #we just need to know the exit status
    retc = os.system("rdate -p %s &>/dev/null" % server)

    return retc == 0

def get_servers_from_config(conf_file_path=NTP_CONFIG_FILE,
                            srv_regexp=SRV_LINE_REGEXP):
    """
    Goes through the chronyd's configuration file looking for lines starting
    with 'server'.

    @return: servers found in the chronyd's configuration
    @rtype: list

    """

    ret = list()

    try:
        with open(conf_file_path, "r") as conf_file:
            line = conf_file.readline()
            while line:
                match = srv_regexp.match(line)
                if match:
                    ret.append(match.group(1))

                line = conf_file.readline()

    except IOError as ioerr:
        msg = "Cannot open config file %s for reading (%s)" % (conf_file_path,
                                                               ioerr.strerror)
        raise NTPconfigError(msg)

    return ret

def save_servers_to_config(servers, conf_file_path=NTP_CONFIG_FILE,
                           srv_regexp=SRV_LINE_REGEXP, out_file_path=None):
    """
    Replaces the servers defined in the chronyd's configuration file with
    the given ones. If the out_file is not None, then it is used for the
    resulting config.

    @type servers: iterable
    @param out_file_path: path to the file used for the resulting config

    """

    try:
        old_conf_file = open(conf_file_path, "r")

    except IOError as ioerr:
        msg = "Cannot open config file %s for reading (%s)" % (conf_file_path,
                                                               ioerr.strerror)
        raise NTPconfigError(msg)

    try:
        if out_file_path:
            new_conf_file = open(out_file_path, "w")
        else:
            (fildes, temp_path) = tempfile.mkstemp()
            new_conf_file = os.fdopen(fildes, "w")

    except IOError as ioerr:
        if out_file_path:
            msg = "Cannot open new config file %s "\
                  "for writing (%s)" % (out_file_path, ioerr.strerror)
        else:
            msg = "Cannot open temporary file %s "\
                  "for writing (%s)" % (temp_path, ioerr.strerror)

        raise NTPconfigError(msg)

    heading = "# These servers were defined in the installation:\n"

    #write info about the origin of the following lines
    new_conf_file.write(heading)

    #write new servers
    for server in servers:
        new_conf_file.write("server " + server + " iburst\n")

    #copy non-server lines from the old config and skip our heading
    line = old_conf_file.readline()
    while line:
        if not srv_regexp.match(line) and line != heading:
            new_conf_file.write(line)

        line = old_conf_file.readline()

    if not out_file_path:
        try:
            stat = os.stat(conf_file_path)
            os.rename(temp_path, conf_file_path)
            os.chmod(conf_file_path, stat.st_mode)

        except OSError as oserr:
            msg = "Cannot replace the old config with "\
                  "the new one (%s)" % (oserr.strerror)

            raise NTPconfigError(msg)

    old_conf_file.close()
    new_conf_file.close()