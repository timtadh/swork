#Swork - the project management utility.
#Author: Tim Henderson
#Contact: tim.tadh@gmail.com,
    #or via EECS Department of Case Western Reserve University, Cleveland Ohio
#Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE

import os, sys, tempfile, psutil

## A bunch of cheese to make this more portable around different json libs.
try:
    import json
except ImportError:
    import simplejson as json

if hasattr(json, 'load'):
    json_load = json.load
else:
    def json_load(f):
        data = f.read()
        return json.read(data)

tmpdir = tempfile.gettempdir()
datadir = os.path.join(tmpdir, 'swork')
homedir = os.path.abspath(os.environ.get('HOME', ''))
rcfile = os.path.join(homedir, '.sworkrc')

def log(s):
    sys.stderr.write(str(s))
    sys.stderr.write('\n')
    sys.stderr.flush()

def output(s):
    sys.stdout.write(str(s))
    sys.stdout.write('\n')
    sys.stdout.flush()

## A utility function stolen from:
# http://stackoverflow.com/questions/1158076/implement-touch-using-python/1160227#1160227
def touch(fname, times = None):
    fhandle = file(fname, 'a')
    try:
        os.utime(fname, times)
    finally:
        fhandle.close()

def ttydir():
    tty = os.ttyname(sys.stdin.fileno())
    tty = tty.replace('/dev/', '').replace(os.path.sep, '_')
    tty = tty + '_' + str(psutil.Process(os.getppid()).ppid)
    ttydir = os.path.join(datadir, tty)
    if not os.path.exists(datadir):
        os.mkdir(datadir)
    if not os.path.exists(ttydir):
        os.mkdir(ttydir)
    return ttydir

def usefiles(files):
    d = ttydir()
    for fname in files:
        touch(os.path.join(d, fname))
    return lambda f: f

def getfile(fname):
    return os.path.join(ttydir(), fname)

def file_empty(fname):
    return not bool(os.path.getsize(getfile(fname)))

def dumpenv():
    envname = getfile('env')
    log('saving enviroment to ... %s' % envname)
    env = open(envname, 'w')
    try:
        collect = list()
        for name,data in os.environ.iteritems():
            collect.append(':'.join((name, data.encode('hex'))))
        data = '\n'.join(collect)
        env.write(data)
    finally:
        env.close()

def loadenv():
    env = open(getfile('env'), 'r')
    try:
        data = env.read()
    finally:
        env.close()
    d = dict()
    for line in data.split('\n'):
        name, value = line.split(':', 1)
        d.update({name:value.decode('hex')})
    return d

def setenv(env):
    collect = list()
    unset = 'unset %s;'
    export = "export %s='%s';"

    for name in os.environ.keys():
        collect.append(unset % name)

    for name,val in env.iteritems():
        collect.append(export % (name, val))

    return '\n'.join(collect)

def restore_env():
    output(setenv(loadenv()))

def loadrc():
    if not os.path.exists(rcfile):
        log('no rc file exists looked at: %s' % rcfile)
        log('cannot continue please make an rcfile')
        return False
    f = open(rcfile, 'r')
    try:
        data = json_load(f)
    finally:
        f.close()
    return data
