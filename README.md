SWORK
=====

by Tim Henderson (tim.tadh@gmail.com)

## Table of Contents

1. Introduction
2. Examples
3. Install
4. Usage

Introduction
============

Command line utility to start up enviroments for particular projects. Project
configuration scripts can be any executable file and are associated with a
particular project via ~/.sworkrc file. The utility saves the enviroment
variables that exist before its execution and restores them as necessary. It can
also call teardown scripts as necessary when switching projects (or restoring
the original shell).

I have previously written very complex enviroment management tools for
particular projects.  Facing the prospect of making yet another project specific
tool, I decided to write a general purpose extensible tool.

Swork is licensed under the terms of GPLv2, see the license file for details.

#### Current Limitations

swork only supports the Bash shell right now. It would be fairly trivially to
add another shell however, I will only do so if there is a user for it. If you
would like to swork with another shell besides bash please email me. (or you
know this is the 2011 you could fork it and add it yourself).

swork may also support zsh although this is entirely untested.

Examples
========

Add a project:

    $ cd to a project directory
    $ sw add project_name
    
you will be prompted to write scripts for startup and teardown. The scripts you
write will be saved to the projects directory as `.swork.activate` and
`.swork.deactivate`. (You can add project manually and customize them further by
editing `~/.sworkrc`)

List your projects:

    $ sw list
    project1
        root : /path/to/code/project1
        start_cmd : echo 'project1 setup'; source .swork.activate
        teardown_cmd : echo 'project1 teardown'; source .swork.deactivate
    project2
        root : /path/to/code/project2
        start_cmd : echo 'project2 setup'; source .swork.activate
        teardown_cmd : echo 'project2 teardown'; source .swork.deactivate

Setup the enviroment:

    $ sw start project1

This saves all the enivroment variables and sources `start_cmd` in the
configuration file (`.sworkrc`).

Restore the original enviroment:

    $ sw restore

cd to a project:

    $ sw cd proj1
    $ pwd
    /path/to/proj1

cd to a sub-dir of a project:

    $ sw cd proj1/sub/directory
    $ pwd
    /path/to/proj1/sub/directory

Finally you can have swork automatically cd to a project sub-dir when starting a
project by:

    $ swork start -c proj1/sub/dir
    $ pwd
    /path/to/proj1/sub/dir


Install
=======

first use pip to install the packages (this installs the current stable version
0.3). If you would like to install the master remove "@r0.3". Or simply update
aftwards with `swork update [-s] --release=master`.

    pip install psutil # this is not done automatically for some reason...
    pip install --src="$HOME/.src" -e git://github.com/timtadh/swork.git@r0.3#egg=swork

then modify your .bashrc to make the command an alias for

    source swork [args]

I call my alias `sw` for convience eg.

    alias sw="source `which swork`"

for the lazy

    echo 'alias sw="source `which swork`"' >> ~/.bashrc

Now to get started using `swork` add a project!

    $ cd to a project
    $ sw add project_name

### Updating, Staying Current

You can update one of two ways. First you can use the built in update command.
Giving it the sudo option causes it to automatically preprend sudo to the
generated command. This checks out the head of the release branch you are on.
(eg. 0.2). See the Usage section for more details on the update command.

    sw update [--sudo]

The other way is to use pip. The command below is an example command, and is in
fact the command generated by `swork update`.

    pip install --src="$HOME/.src" --upgrade -e git://github.com/timtadh/swork.git@r0.2#egg=swork

You can check if there are updates available using:

    sw update [--sudo] --check

Note: You will need to use `--sudo` when updating and checking for updates if
you installed `swork` as root. 

Usage
=====

    usage: swork [-h] [start|add|restore|list|cd|update] [project_name]

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

      update                           starts auto updater
        --sudo                         use the sudoed version of the update command
        --release=<rel-num>            which release eg. "master", "0.2" etc.
        --src=<dir>                    what directory should it check the source
                                           into defaults to $HOME/.src/

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


