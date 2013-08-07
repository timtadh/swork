#!/usr/bin/env python
'''
Swork - the project management utility.
Author: Tim Henderson
Contact: tim.tadh@gmail.com,
    or via EECS Department of Case Western Reserve University, Cleveland Ohio
Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE
'''

short_usage_message = \
'''usage: swork [-h] [start|add|restore|list|cd|update] [project_name]'''

usage_message = \
'''
setups the enviroment to work on a particular project

flags:
  -h                               shows help message
  --help                           show an extended help message

sub commands:

  start <project_name>             sets up the enviroment for *project_name*
    -c                             start and cd into a directory relative to the
                                       root eg.
                                       start -c project_name/some/sub/dir
  
  add <project_name>               adds a new project. uses current directory as
                                   the root. prompts for scripts

  restore                          restores the original enviroment for the
                                       shell

  list                             list the available projects

  cd project_name [sub-path]       cd into a directory relative to the root
     project_name[/sub-path]           directory of *project_name*

  path project_name[/sub-path]     echo out the full path

  update                           starts auto updater
    --sudo                         use the sudoed version of the update command
    --release=<rel-num>            which release eg. "master", "0.2" etc.
    --src=<dir>                    what directory should it check the source
                                       into defaults to $HOME/.src/
    --check                        check to see if updates are needed. takes
                                       into account the value of the other
                                       flags. eg. If release is a different
                                       release it will check if updating matters
                                       based on whether or not they are at the
                                       same commit. Only "commit" is ignored.
    --commit=<commitid>            updates to a specific commit.
'''

extended_message = \
'''rc-file:
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

cd to a project:
$ swork cd proj1
$ pwd
/path/to/proj1

cd to a sub-dir of a project:
$ swork cd proj1 sub/directory
$ pwd
/path/to/proj1/sub/directory

alternate syntax:
$ swork cd proj1/sub/directory
$ pwd
/path/to/proj1/sub/directory

'''

import sys, os
from subprocess import check_output as run
from getopt import getopt, GetoptError
import sworklib
from sworklib import log, output
import swork_version

CWD = os.environ.get('PWD', os.getcwd())
sworklib.usefiles(['env', 'cur'])
EDITOR = os.getenv('EDITOR')
RELEASE = swork_version.RELEASE
SRC_DIR = "$HOME/.src"
UPDATE_CMD = (
  'pip install --src="%s" --upgrade -e '
  'git://github.com/timtadh/swork.git@%s#egg=swork'
)

error_codes = {
    'version':0,
    'usage':1,
    'option':2,
    'list':3,
    'rcfile':4,
    'dupname':5,
}

def command(f):
    '''A decorator to mark a function as shell sub-command.'''
    setattr(f, 'command', True)
    return f

def usage(code=None):
    '''Prints the usage and exits with an error code specified by code. If code
    is not given it exits with error_codes['usage']'''
    log(short_usage_message)
    if code is None or code < 2:
        log(usage_message)
    if code is None:
        log(extended_message)
        code = error_codes['usage']
    sys.exit(code)

@command
def cd(args):
    '''cd to the root directory, or to the sub-directory indicated'''
    if len(args) < 1:
        log('cd requires a project_name, you gave %s' % str(args))
        usage(error_codes['option'])
    project_name = args[0]
    next = ''
    if os.path.sep in project_name:
        project_name, next = project_name.split(os.path.sep, 1)
    rc = sworklib.loadrc()
    if rc == False:
        usage(error_codes['rcfile'])
    if project_name not in rc:
        log('the project %s is not defined' % project_name)
        sys.exit(error_codes['rcfile'])
    proj = rc[project_name]
    root = proj['root']

    if next == '' and len(args) == 2:
        next = args[1]
    output("cd %s" % os.path.join(root, next))

@command
def path(args):
    '''echo the path to the root directory, or to the sub-directory indicated'''
    if len(args) < 1:
        log('cd requires a project_name, you gave %s' % str(args))
        usage(error_codes['option'])
    project_name = args[0]
    next = ''
    if os.path.sep in project_name:
        project_name, next = project_name.split(os.path.sep, 1)
    rc = sworklib.loadrc()
    if rc == False:
        usage(error_codes['rcfile'])
    if project_name not in rc:
        log('the project %s is not defined' % project_name)
        sys.exit(error_codes['rcfile'])
    proj = rc[project_name]
    root = proj['root']

    if next == '' and len(args) == 2:
        next = args[1]

    if next:
        output("echo %s" % os.path.join(root, next))
    else:
        output("echo %s" % root)

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
def add(args):
    '''adds a new project.'''

    if len(args) > 1 or len(args) == 0:
        log("need to specify project name")
        usage(error_codes['option'])
    
    rc = sworklib.loadrc(True)
    if rc == False:
        rc = dict()

    name = args[0]
    if name in rc:
        log("already a project with the name %s" % name)
        usage(error_codes['dupname'])
    
    root = os.getcwd()
    start = "echo '%s setup'; source .swork.activate" % name
    end = "echo '%s teardown'; source .swork.deactivate" % name
    sworklib.edittext(EDITOR, path='.swork.activate')
    sworklib.edittext(EDITOR, path='.swork.deactivate')
    sworklib.addproj(name, root, start, end)

@command
def start(args):
    '''excutes the start command.'''

    try:
        opts, args = getopt(args, 'c', ['cd'])
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    cd = False
    for opt, arg in opts:
        if opt in ('-c', '--cd'):
            cd = True

    if len(args) < 1:
        log('start requires a project_name')
        usage(error_codes['option'])

    next = ''
    if cd and os.path.sep in ' '.join(args):
        project_name, next = ' '.join(args).split(os.path.sep, 1)
    else:
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
    output('export SW_PROJECT_ROOT=%s' % (root))
    output('cd %s' % (root))
    output('%s' % (cmd))
    output('cd %s' % (CWD))
    sworklib.pushproj(project_name)
    if cd:
        output("cd %s" % os.path.join(root, next))

@command
def restore():
    '''restores the shell to its original state.'''
    sworklib.popproj()
    sworklib.restore_env()
    output('cd %s' % (CWD))

def check_update(src_dir, sudo, release):
    if release[0].isdigit(): release = 'r' + release
    src_dir = os.path.abspath(os.path.expandvars(src_dir))
    local = 'master' # for some reason pip always has the master branch
                     # be whatever the user is using. Eg. the user may be
                     # on r0.3 but the git repository git manages will
                     # call that branch 'master' even though the contents
                     # are r0.3. Therefore, we always compare to the local
                     # master
    remote = 'refs/remotes/origin/' + release
    run(['sudo', 'git', '--git-dir=%s/swork/.git' % src_dir, 'fetch', 
      'origin', "%s:%s" % (release,remote)])
    lmsg = run(['git', '--git-dir=%s/swork/.git' % src_dir, 'show-branch',
      '--sha1-name', local])
    rmsg = run(['git', '--git-dir=%s/swork/.git' % src_dir, 'show-branch',
      '--sha1-name', remote])
    def getcommit(msg):
        return msg.replace('[','').replace(']','').split(' ', 1)[0]
    if getcommit(lmsg) == getcommit(rmsg):
        log('No update needed already using the latest %s' % release)
    else:
        log('update needed to use the latest %s' % release)

@command
def update(args):
    try:
        opts, args = getopt(
            args, 'sr:', ['sudo', 'check', 'src=', 'release=', 'commit='])
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    sudo = False
    src_dir = SRC_DIR
    release = RELEASE
    commit = None
    check = False
    for opt, arg in opts:
        if opt in ('-s', '--sudo'):
            sudo = True
        elif opt in ('-r', '--release'):
            release = arg
        elif opt in ('--src',):
            src_dir = arg
        elif opt in ('--commit',):
            commit = arg
        elif opt in ('--check',):
            check = True

    if check:
        check_update(src_dir,sudo,release)
        sys.exit(0)

    if release[0].isdigit():
        release = 'r' + release
    release = 'origin/' + release

    if commit is not None:
        cmd = UPDATE_CMD % (src_dir, commit)
    else:
        cmd = UPDATE_CMD % (src_dir, release)

    if sudo:
        output('sudo %s' % cmd)
    else:
        output(cmd)

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
        opts, args = getopt(sys.argv[1:], 'hv', ['help', 'version'])
    except GetoptError, err:
        log(err)
        usage(error_codes['option'])

    for opt, arg in opts:
        if opt in ('-h',):
            usage(error_codes['usage'])
        elif opt in ('--help',):
            usage()
        elif opt in ('-v', '--version'):
            log(RELEASE)
            sys.exit(error_codes['version'])

    if len(args) == 0:
        log('A subcommand is required')
        usage(error_codes['option'])

    sub_cmd = args[0]
    if sub_cmd not in commands:
        log('command %s is not available' % sub_cmd)
        usage(error_codes['option'])

    if sub_cmd != 'path':
        if sworklib.file_empty('env'):
            sworklib.dumpenv()

    cmd = commands[sub_cmd]
    if cmd.func_code.co_argcount == 1:
        cmd(args[1:])
    else:
        cmd()


if __name__ == '__main__':
    main()

