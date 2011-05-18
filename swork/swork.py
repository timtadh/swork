#!/usr/bin/env python
'''
Swork - the project management utility.
Author: Tim Henderson
Contact: tim.tadh@gmail.com,
    or via EECS Department of Case Western Reserve University, Cleveland Ohio
Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE
'''
print 'hello'

usage_message = \
'''usage: swork [-hl] [start|restore|list] [project_name]

setups the enviroment to work on a particular project

flags:
  -h, --help                       show this help message

sub commands:
  start project_name               sets up the enviroment for *project_name*
  restore                          restores the original enviroment for the shell
  list                             list the available projects

Examples:

Start working on a project call, day_job
$ swork start day_job

Stop working on the last started project and restore the shell to the original
state:
$ swork restore

'''

import sys
from subprocess import check_call as run
from getopt import getopt, GetoptError

error_codes = {
    'usage':1,
    'option':2,
    'list':3,
}

def command(f):
  setattr(f, 'command', True)
  return f

def usage(code=None):
    print usage_message
    if code is None:
        code = error_codes['usage']
    sys.exit(code)

@command
def list():
    print 'stub for listing projects'
    sys.exit(error_codes['list'])

@command
def start(args):
    if len(args) != 1:
        print 'start requires a project_name'
        usage(error_codes['option'])
    print 'stub for starting a project'

@command
def restore():
    print 'stub for restoring the shell'

commands = dict((name, attr)
  for name, attr in locals().iteritems()
  if hasattr(attr, 'command') and attr.command == True
)

def main():
    try:
        opts, args = getopt(sys.argv[1:], 'h', ['help'])
    except GetoptError, err:
        print str(err)
        usage(error_codes['option'])

    for opt, arg in opts:
        if opt in ('-h', '--help'):
             usage()

    if len(args) == 0:
        print 'A subcommand is required'
        usage(error_codes['option'])

    sub_cmd = args[0]
    if sub_cmd not in commands:
        print 'command %s is not available'
        usage(error_codes['option'])

    cmd = commands[sub_cmd]
    if cmd.func_code.co_argcount == 1:
        cmd(args[1:])
    else:
        cmd()


if __name__ == '__main__':
    main()

