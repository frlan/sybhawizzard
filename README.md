sybhawizzward
-------------

About
=====

sybhawizzward is helping you enabling HA on a SQLAnywhere database by
preparing the needed SQL queries and -- if you like -- direct sending
them to the database(s). Not a huge piece of rocketscience, but fasts
up your deployment and, due to the fact that you need to write done a
project file for, it's forcing your to document your setup at least on
a very basic level.


Usage
=====

sybhawizzward.py [options]

Options are:
-a to direct apply the SQL (dangerous!)
-o <pathname> writes generated SQL to given pathname
-p <projectfile> file to store information about setup


Installation & Dependencies
===========================

This tool is based on Python and SQLAnyhwere. Therefore you will need
- Python in a recent version
- sqlanydb-Python-Modul installed and set up (in case of you want to
  direct apply the SQL)

To install the script, just place it somewhere (or just keep it inside
this folder). No further installation needed. For some tricks and hacks
e.g. according to database configuration check the corrosponding part
of this README.


Writing an ini file
===================

You can find an exmaple.ini inside the distribution of this little
tool. This might help you setting up your own file.

Start with the servers present in your setup. A line for a server might
look like:

[server_x]
name = <a server name>
hostname = <hostname or IP>
port = <port server is listen on>
statepath = <server local path where to put state files; Finish with
path delimiter>

For each server your need inside your setup, count server_x up starting
with server_0. Put also the server for the Arbiter into this list.

So having 3 servers inside your setup incl. the designated arbiter, you
should have server_0, server_1 and server_2.

Having this done, you need to create entries for databases which should
be part of the HA cluster. This is quiet similar to server
configurations.

Add behind the server sections:

[database_x]
name = <name of database>
auth_string = <string, which shall be used for HA -- keep ir secret!>
server1 = <first server involved in cluster>
server2 = <second server involced in cluster>
arbiter = <arbiter for the database>
unload_path = <path to unload main database to; Finish with path delimiter>

Similar to server, start with x=0 so the first entry is [database_0].
Theoretical you can mix up servers and databases on writing your
ini-file, but you have to keep care to define the server first. At
minimum with an empty entry.

Even an Arbiter is also a server, keep care to use its entry only in
prupose of setting up an Arbiter. Inside logic, there are little
differences on dealing with an Arbiter-server and a normal database
server.
