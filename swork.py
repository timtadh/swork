#!/usr/bin/env python
'''
Swork - the project management utility.
Author: Tim Henderson
Contact: tim.tadh@gmail.com,
    or via EECS Department of Case Western Reserve University, Cleveland Ohio
Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE
'''

config_message = \
'''The RC File.

Swork is capable of setting up its own configuration file. (Just use the `add`
command). However, here is now the configuration file is structured in case you
want to edit it.

Location: `$HOME/.sworkrc`

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

- project_name is a string and the name of the project.
- root is the file system path to the root directory of the project.
- start_cmd will be sourced by the shell on startup.
- teardown_command will be sourced by the shell at teardown.

`sw add` uses the following templates to generate start_cmd/teardown_cmd(s)

    echo "start/stop <project-name>"; source <path-to-[de]activate>

'''

examples_message = \
'''Some Examples

$ # add a project
$ cd /path/to/project
$ sw add my_project

$ # Start working on a project called day_job
$ swork start day_job

$ # Stop working on the last started project and restore the shell to the
$ # original state:
$ swork restore

$ # cd to a project:
$ swork cd proj1
$ pwd
/path/to/proj1

$ # cd to a sub-dir of a project:
$ swork cd proj1/sub/directory
$ pwd
/path/to/proj1/sub/directory

$ # start and cd to a project sub dir
$ sw start -c project/sub/dir
$ pwd
/path/to/proj1/sub/dir

'''

import sys, os
from subprocess import check_output as run
from getopt import getopt, GetoptError

import optutils
from optutils import log, output, error_codes, add_code

import sworklib
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

add_code('version')
add_code('option')
add_code('list'); error_codes['list'] = 126
add_code('rcfile')
add_code('dupname')


def version():
    '''Print version and exit'''
    log('swork version :', RELEASE)
    sys.exit(error_codes['version'])


def parse_project(spec):
    if os.path.sep in spec:
        return spec.split(os.path.sep, 1)
    return spec, ''


def load_project(project_name):
    rc = sworklib.loadrc()
    if rc == False:
        log("Couldn't load the rcfile")
        sys.exit(error_codes['rcfile'])
    if project_name not in rc:
        log('the project %s is not defined' % project_name)
        sys.exit(error_codes['rcfile'])
    return rc[project_name]


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


@optutils.main(
    'usage: swork [-h] [start|add|restore|list|cd|update] [project_name]',
    '''
    setups the enviroment to work on a particular project

    Options
         -h, help                      shows help message
         --help-config                 show the help on the config file
         --help-examples               show some usage examples
    ''',
    'hv',
    ['help',
     'help-config',
     'help-examples',
     'version'],
)
def main(argv, util, parser):

    ## PS1 not being available is a strong indication this file wasn't sourced
    ## correctly
    if 'PS1' not in os.environ:
        log('*'*72)
        log(' '*10, 'WARNING - you should run this by sourcing swork.')
        log(' '*3,
        '''try running: echo 'alias sw="source `which swork`"' >> ~/.bashrc''')
        log('*'*72)
        log()

    if sworklib.file_empty('env'):
        sworklib.dumpenv()


    @util.command(
        'add a new project.',
        '''
        sw add [-a ./.activate] [-d ./.deactivate] <project-name>

        Options
            -h, help                  Show this help message
            -a, activate=<path>       Activate file
            -d, deactivate=<path>     Deactivate file
            --no-create               Don't create any files

        When `--no-create` is given the system will not create any files (except
        for the `$HOME/.sworkrc` file if it does not already exist. However, it
        will *use* the activate/deactivate files if they are passed in via the
        flags. You can use this to setup a project that already has a project
        specific activation file to be managed by `swork`.

        Specs
            <project-name>
                Name of the project to add.
            <path>
                File system path to regular file.
        ''',
        'ha:d:',
        ['help','activate','deactivate','no-create'],
    )
    def add(argv, util, parser):
        '''adds a new project.'''

        activate = None
        deactivate = None
        no_create = False
        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help',):
                util.usage()
            elif opt in ('-a','--activate',):
                activate = util.assert_file_exists(arg)
            elif opt in ('-d','--deactivate',):
                deactivate = util.assert_file_exists(arg)
            elif opt in ('--no-create',):
                no_create = True

        if len(args) > 1 or len(args) == 0:
            log("need to specify project name")
            util.usage(error_codes['option'])

        rc = sworklib.loadrc(True)
        if rc == False:
            rc = dict()

        name = args[0]
        if name in rc:
            log("already a project with the name %s" % name)
            util.usage(error_codes['dupname'])

        if activate is None and not no_create:
            activate = '.swork.activate'
            sworklib.edittext(EDITOR, path=activate)
        if deactivate is None and not no_create:
            deactivate = '.swork.deactivate'
            sworklib.edittext(EDITOR, path=deactivate)

        activate = '' if activate is None else 'source %s' % activate
        deactivate = '' if deactivate is None else 'source %s' % deactivate

        root = os.getcwd()
        start = "echo '%s setup'; %s " % (name, activate)
        end = "echo '%s teardown'; %s " % (name, deactivate)
        sworklib.addproj(name, root, start, end)


    @util.command(
        'remove a project from the rc file.',
        '''
        sw rm <project-name>

        Options
            -h, help                  Show this help message

        Specs
            <project-name>
                Name of the project to add.
        ''',
        'h',
        ['help'],
    )
    def rm(argv, util, parser):
        '''adds a new project.'''

        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help',):
                util.usage()

        if len(args) > 1 or len(args) == 0:
            log("need to specify project name")
            util.usage(error_codes['option'])

        rc = sworklib.loadrc(True)
        if rc == False:
            rc = dict()

        name = args[0]
        if name not in rc:
            log("project '%s' not in the rc file" % name)
            util.usage(error_codes['dupname'])

        log("Are you sure you want to remove %s? [yes|no]" % name, )
        sure = raw_input()
        if sure == "yes":
            log("removing %s" % name)
            sworklib.rmproj(name)
        elif sure[0].lower() == "y":
            log("type 'yes' to remove, cowardly exiting")
        else:
            log("did not remove the project %s" % name)


    @util.command(
        'List all available projects.',
        '''
        sw list

        Lists all the projects in the .sworkrc file.

        Options

            -h, help                 Print this message
        ''',
        'h',
        ['help'],
    )
    def list(argv, util, parser):
        '''Lists all available projects.'''

        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help',):
                util.usage()

        rc = sworklib.loadrc()
        if rc == False:
            log("Couldn't load the rcfile")
            util.usage(error_codes['rcfile'])
        for name, proj in rc.iteritems():
            log(name)
            log(' '*4 + 'root : ' + proj['root'])
            log(' '*4 + 'start_cmd : ' + proj['start_cmd'])
            log(' '*4 + 'teardown_cmd : ' + proj['teardown_cmd'])
        sys.exit(error_codes['list'])


    @util.command(
        'Restores the original environment for the shell',
        '''
        sw restore

        Restores the original shell environment. This unsets all the set
        envirnoment variables and sets the originals. It does not do anything to
        defined functions. Those must be handled manually in deactivate scripts.

        Options
            -h, help                 Print this message
        ''',
        'h',
        ['help']
    )
    def restore(argv, util, parser):
        '''restores the shell to its original state.'''

        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help',):
                util.usage()

        sworklib.popproj()
        sworklib.restore_env()
        output('cd %s' % (CWD))


    @util.command(
        'start work on a project',
        '''
        sw start [-c] <project-name>[/path/to/sub/dir]

        This first checks to see if an swork project is currently active. If it
        is it restores the state. Otherwise, it ensures the orginal state is
        saved and sources the project's activate script.

        Examples

            $ sw start project
            $ sw start -c project
            $ sw start -c project/src/main

        Options
            -h                        Print this message
            -c                        Also cd to the project
        ''',
        'hc',
        ['help', 'cd']
    )
    def start(argv, util, parser):

        cd = False
        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help'):
                util.usage()
            elif opt in ('-c', '--cd'):
                cd = True

        if len(args) < 1:
            log('start requires a project_name')
            util.usage(error_codes['option'])

        next = ''
        if cd:
            project_name, next = parse_project(' '.join(args))
        else:
            project_name = ' '.join(args)

        proj = load_project(project_name)
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


    @util.command(
        'echo the path to the project ',
        '''
        sw path project[/path/to/sub/dir]

        Echos the path to the projects root or subdirectory.

        Examples

            $ sw path project
            /abs/path/to/project
            $ sw path project/path/to/sub/dir
            /abs/path/to/project/path/to/sub/dir
            $ cp file $(sw path project/sub/dir)

        Options

            -h, help                        Print this message
        ''',
        'h',
        ['help']
    )
    def path(argv, util, parser):

        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help',):
                util.usage()

        if len(args) < 1:
            log('path requires a project_name, you gave %s' % str(args))
            util.usage(error_codes['option'])
        project_name, next = parse_project(args[0])

        proj = load_project(project_name)
        root = proj['root']

        if next:
            output("echo %s" % os.path.join(root, next))
        else:
            output("echo %s" % root)


    @util.command(
        'cd the path to the project ',
        '''
        sw cd project[/path/to/subdir]

        Cd's to a project without touching the environment.

        Examples

              $ sw cd project
              eg. cd /abs/path/to/project

              $ sw cd project/sub/dir
              eg. cd /abs/path/to/project/sub/dir

        Options
            -h, help                Print this message
        ''',
        'h',
        ['help']
    )
    def cd(argv, util, parser):

        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h',):
                util.usage()

        if len(args) < 1:
            log('cd requires a project_name, you gave %s' % str(args))
            util.usage(error_codes['option'])
        project_name, next = parse_project(args[0])

        proj = load_project(project_name)
        root = proj['root']

        if next:
            output("cd %s" % os.path.join(root, next))
        else:
            output("cd %s" % root)


    @util.command(
        'start the autoupdater',
        '''
        sw update [--check] [--src=$HOME/.src] [--release=<branch>]
                  [--commit=<commit>] [--sudo]

        Allows for automatic updating of this program.

        Options
            --sudo                     use the sudoed version of the update command
            --release=<rel-num>        which release eg. "master", "0.2" etc.
            --src=<dir>                what directory should it check the source
                                       into defaults to $HOME/.src/
            --check                    check to see if updates are needed. takes
                                       into account the value of the other
                                       flags. eg. If release is a different
                                       release it will check if updating matters
                                       based on whether or not they are at the
                                       same commit. Only "commit" is ignored.
            --commit=<commitid>        updates to a specific commit.
        ''',
        'hsr:',
        ['help', 'sudo', 'check', 'src=', 'release=', 'commit='],
    )
    def update(argv, util, parser):

        sudo = False
        src_dir = SRC_DIR
        release = RELEASE
        commit = None
        check = False
        opts, args = parser(argv)
        for opt, arg in opts:
            if opt in ('-h','--help'):
                util.usage()
            elif opt in ('-s', '--sudo'):
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


    opts, args = parser(argv)
    for opt, arg in opts:
        if opt in ('-h','--help',):
            util.usage()
        elif opt in ('--help-config',):
            log(config_message)
            sys.exit(error_codes['usage'])
        elif opt in ('--help-examples',):
            log(examples_message)
            sys.exit(error_codes['usage'])
        elif opt in ('-v', '--version'):
            version()

    util.run_command(args)


if __name__ == '__main__':
    main(sys.argv[1:])

