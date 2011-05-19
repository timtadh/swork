#!/usr/bin/env python
'''
Swork - the project management utility.
Author: Tim Henderson
Contact: tim.tadh@gmail.com,
    or via EECS Department of Case Western Reserve University, Cleveland Ohio
Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE
'''

usage_message = \
'''usage: swork [-hl] [start|restore|list] [project_name]

setups the enviroment to work on a particular project

flags:
  -h, --help                       show this help message

sub commands:
  start project_name               sets up the enviroment for *project_name*
  restore                          restores the original enviroment for the shell
  list                             list the available projects

rc-file:
  To use you must setup an rc file in you home directory.
  eg.
    $ touch ~/.sworkrc
the contents should be something like:
    {
        "project1" : {
            "root":"/path/to/project/root",
            "start_cmd":"source /path/to/project/root/then/setenv"
            "teardown_cmd":"echo 'project1 teardown'"
        },
        "project2" : {
            "root":"/path/to/project/root",
            "start_cmd":"source /path/to/project/root/then/setenv"
            "teardown_cmd":"echo 'project2 teardown'"
        }
    }
The contents must be valid json (as recognized by the python json lib) and
must have the schema:
    project_name1 ->
        root -> string
        start_cmd -> string
        teardown_cmd -> string
    project_name2 ->
        root -> string
        start_cmd -> string
        teardown_cmd -> string
where project_name can be any string (including the empty string).

Examples:

Start working on a project call, day_job
$ swork start day_job

Stop working on the last started project and restore the shell to the original
state:
$ swork restore

'''

import sys, os
from subprocess import check_call as run
from getopt import getopt, GetoptError
import sworklib
from sworklib import log, output

CWD = os.environ.get('PWD', os.getcwd())
sworklib.usefiles(['env', 'cur'])

error_codes = {
    'usage':1,
    'option':2,
    'list':3,
    'rcfile':4,
}

def command(f):
    '''A decorator to mark a function as shell sub-command.'''
    setattr(f, 'command', True)
    return f

def usage(code=None):
    '''Prints the usage and exits with an error code specified by code. If code
    is not given it exits with error_codes['usage']'''
    log(usage_message)
    if code is None:
        code = error_codes['usage']
    sys.exit(code)

@command
def list():
    '''Lists all available projects.'''
    rc = sworklib.loadrc()
    if rc == False:
        usage(error_codes['rcfile'])
    for name, proj in rc.iteritems():
        log(name)
        log(' '*4 + 'root : ' + proj['root'])
        log(' '*4 + 'start_cmd : ' + proj['start_cmd'])
        log(' '*4 + 'teardown_cmd : ' + proj['teardown_cmd'])

@command
def start(args):
    '''excutes the start command.'''
    if len(args) != 1:
        log('start requires a project_name')
        usage(error_codes['option'])
    project_name = args[0]
    rc = sworklib.loadrc()
    if rc == False:
        usage(error_codes['rcfile'])
    if project_name not in rc:
        log('the project %s is not defined' % project_name)
        sys.exit(error_codes['rcfile'])
    proj = rc[project_name]
    cmd = proj['start_cmd']
    root = proj['root']

    sworklib.popproj()
    sworklib.restore_env()
    output('cd %s' % (root))
    output('%s' % (cmd))
    output('cd %s' % (CWD))
    sworklib.pushproj(project_name)

@command
def restore():
    '''restores the shell to its original state.'''
    sworklib.popproj()
    sworklib.restore_env()
    output('cd %s' % (CWD))

commands = dict((name, attr)
  for name, attr in locals().iteritems()
  if hasattr(attr, 'command') and attr.command == True
)

def main():
    ## PS1 not being available is a strong indication this file wasn't sourced correctly
    if 'PS1' not in os.environ:
        log('WARNING - you should run this by sourcing swork.')

    ## getopt setup
    try:
        opts, args = getopt(sys.argv[1:], 'hc', ['help', 'check'])
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    check = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
             usage()
        elif opt in ('-c', '--check'):
             check = True

    if len(args) == 0:
        log('A subcommand is required')
        usage(error_codes['option'])

    sub_cmd = args[0]
    if sub_cmd not in commands:
        log('command %s is not available' % sub_cmd)
        usage(error_codes['option'])

    if sworklib.file_empty('env'):
        sworklib.dumpenv()

    cmd = commands[sub_cmd]
    if cmd.func_code.co_argcount == 1:
        if not check: cmd(args[1:])
    else:
        if not check: cmd()


if __name__ == '__main__':
    main()

