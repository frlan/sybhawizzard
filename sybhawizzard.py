#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sybhawiz.py
#
#  Copyright 2015-2016 Frank Lanitz <frank@frank.uvena.de>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


from string import Template
import ConfigParser
import argparse


dbistring = (
    'dbisql -c "UID=$user;PWD=$pwd;SERVER=$server_name;DBN=$databasename"'
)
sh_header = '#!/usr/bin/env python\n'


# Little helper function stolen from
# https://wiki.python.org/moin/ConfigParserExamples
def ConfigSectionMap(section, Config):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


class Database():
    def __init__(self, name, auth_string, server1=None, server2=None,
                 arbiter=None, unload_path=None):
        self.name = name
        self.server1 = server1
        self.server2 = server2
        self.arbiter = arbiter
        self.auth_string = auth_string
        self.unload_path = unload_path

    def __get_mirror_name(self, primary):
        """
            Returns a generated name for the database used for either secondary
            or primary server.

            Takes a boolean, where it's the primary dabtase server"""

        name = str()

        if primary is True:
            name = 'primary_' + self.name
        else:
            name = 'mirror_' + self.name

        return name

    def get_mirror_code(self):
        tmp = Template(
            """CREATE MIRROR SERVER \"$server_name\" AS MIRROR """
            """connection_string='SERVER=$server_name;$host1;$host2';""")
        return tmp.substitute(
            server_name=self.__get_mirror_name(False),
            host1=self.server1.host,
            host2=self.server2.host
        )

    def get_primary_code(self):
        tmp = Template(
            """CREATE MIRROR SERVER \"$server_name\" AS PRIMARY """
            """connection_string='SERVER=$server_name;$host1;$host2';"""
        )
        return tmp.substitute(
            server_name=self.__get_mirror_name(True),
            host1=self.server1.host,
            host2=self.server2.host)

    def get_auth_code(self):
        tmp = Template("SET MIRROR OPTION authentication_string='$PWD';")
        return tmp.substitute(
            PWD=self.auth_string)

    def get_partnerserver(self, srv):
        tmp = Template(
            """CREATE MIRROR SERVER \"$servername\" AS PARTNER """
            """connection_string='SERVER=$servername;host=$host' """
            """state_file='$statefile';""")
        return tmp.substitute(
            servername=srv.server_name,
            statefile=srv.statepath + srv.server_name + '.txt',
            host=srv.host)

    def get_complete_create_string(self):
        str = "\n"
        return str.join(
            (
              self.get_partnerserver(self.server1),
              self.get_partnerserver(self.server2),
              self.get_primary_code(),
              self.get_mirror_code(),
              self.arbiter.get_arbiter_code(),
              self.get_auth_code()
              )
            )


class Server():
    def __init__(self, name=None, hostname=None, port=None, statepath=None):
        self.server_name = name
        self.hostname = hostname
        self.port = port
        self.statepath = statepath
        self.host = hostname + ":" + port

    def __str__(self):
        return hostname + ":" + port


class Arbiter(Server):
    def get_arbiter_code(self):
        tmp = Template(
            """CREATE MIRROR SERVER \"$arbiter_name\" AS ARBITER """
            """onnection_string='SERVER=$arbiter_name;HOST=$host'"""
        )
        return tmp.substitute(
            arbiter_name=self.server_name,
            host=self.host)


def main(args):

    parser = argparse.ArgumentParser(description='Creating SQLAnyWhere HA')
    parser.add_argument('-a',
                        help='Apply changes direct. Not yet implemented',
                        action="store_true")
    parser.add_argument('-p', help='Path to projectfile which shall be used')
    parser.add_argument('-o', help='Path output should pe send to')
    args = parser.parse_args()

    filename = args.p
    if filename is None:
        print("Please proivde a project file by  using -p parameter")
        return 1
    servers = {}
    databases = []

    # TPDP: Check, whether file actually exists and close if not
    project = ConfigParser.ConfigParser()
    project.read(filename)

    # First we parse for server, then for databases
    for i in project.sections():
        if i.startswith('server_'):
            map = ConfigSectionMap(i, project)
            if map["name"].startswith("arbiter"):
                servers[i] = Arbiter(
                    name=map["name"],
                    hostname=map["hostname"],
                    port=map["port"],
                    statepath=map["statepath"])
            else:
                servers[i] = Server(
                    name=map["name"],
                    hostname=map["hostname"],
                    port=map["port"],
                    statepath=map["statepath"])
        if i.startswith('database_'):
            map = ConfigSectionMap(i, project)
            tmp = Database(
                    name=map["name"],
                    auth_string=map["auth_string"]
                )
            # Mapping databaes to server
            tmp.server1 = servers[map["server1"]]
            tmp.server2 = servers[map["server2"]]
            tmp.arbiter = servers[map["arbiter"]]
            tmp.unload_path = map["unload_path"]

            databases.append(tmp)

    for i in databases:
        if args.o is not None:
            path = args.o + i.name + '.sql'
            print path
            try:
                f = open(path, 'w')
                f.write(i.get_complete_create_string())
                f.close()
                # Creating SH
                path = args.o + i.name + '.sh'
                print path
                f = open(path, 'w')
                f.write(
                    sh_header + dbistring
                )
                f.close
            except:
                print("Could not write files. Please check output directory")
                return 3
        else:
            print i.get_complete_create_string()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
