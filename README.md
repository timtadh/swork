SWORK
=====

by: Tim Henderson (tim.tadh@gmail.com)

Command line utility to start up enviroments for particular projects. Project configuration scripts
can be any executable file and are associated with a particular project via ~/.sworkrc file. The
utility saves the enviroment variables that exist before its execution and restores them as
necessary.

Swork is still in an early stage but should be useful at the end of today. (hopefully by this
morning in fact). My intention is to incrementally improve it as my needs evolve. I have
previously written very complex enviroment management tools for particular projects. Facing the
prospect of making yet another project specific tool, I decided to write a general purpose
extensible tool.

Swork is licensed under the terms of GPLv2, see the license file for details.

#### Current Limitations

swork only supports the Bash shell right now. It would be fairly trivially to add another shell
however, I will only do so if there is a user for it. If you would like to swork with another shell besides bash please email me. (or you know this is the 2011 you could fork it and add it yourself).

Examples
========

List your projects:

    $ swork list
    hca
        root : /home/hendersont/stuff/Programing/hca
        cmd : source /home/hendersont/stuff/Programing/hca/setenv
    project2
        root : /home/hendersont/stuff/Programing/project2
        cmd : source /home/hendersont/envs/project2

Setup the enviroment:

    $ swork start project_name

Restore the original enviroment

    $ swork restore


Install
=======

first use pip to install the packages

    pip install psutil # this is not done automatically for some reason...
    pip install -e git://github.com/timtadh/swork.git#egg=swork

then modify your .bashrc to make the command an alias for

    source swork [args]

eg.

    alias swork="source `which swork`"

for the lazy

    echo 'alias swork="source `which swork`"' >> ~/.bashrc

### Updating, Staying Current

    pip install --upgrade -e git://github.com/timtadh/swork.git#egg=swork


Usage
=====

    usage: swork [-hl] [start|restore|list] [project_name]

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
                "cmd":"source /path/to/project/root/then/setenv"
            },
            "project2" : {
                "root":"/path/to/project/root",
                "cmd":"source /path/to/project/root/then/setenv"
            }
        }
    The contents must be valid json (as recognized by the python json lib) and
    must have the schema:
        project_name1 ->
            root -> string
            cmd -> string
        project_name2 ->
            root -> string
            cmd -> string
    where project_name can be any string

    Examples:

    Start working on a project call, day_job
    $ swork start day_job

    Stop working on the last started project and restore the shell to the original
    state:
    $ swork restore

