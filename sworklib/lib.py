#Swork - the project management utility.
#Author: Tim Henderson
#Contact: tim.tadh@gmail.com,
    #or via EECS Department of Case Western Reserve University, Cleveland Ohio
#Copyright: 2011 All Rights Reserved, Licensed under the GPLv2, see LICENSE

import os, sys, tempfile, psutil, subprocess

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

shellpid = str(psutil.Process(os.getppid()).ppid())
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

def edittext(editor, text='', path=None):
    unlink = True
    if path is None:
        fd, path = tmpfile()
        f = open(path, 'w')
        f.write(text)
        f.close()
    else:
        assert not text
        unlink = False
        touch(path)
    tty = os.ttyname(sys.stdin.fileno())
    stdout = open(tty, 'w')
    subprocess.check_call([editor, path], stdout=stdout, stdin=sys.stdin)
    f = open(path, 'r')
    s = f.read()
    f.close()
    if unlink:
        os.unlink(path)
    return s.strip()

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
    tty = tty + '_' + shellpid
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

def getfile(fname):
    return os.path.join(ttydir(), fname)

def file_empty(fname):
    return not bool(os.path.getsize(getfile(fname)))

def dumpenv():
    envname = getfile('env')
    #log('saving enviroment to ... %s' % envname)
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

def validaterc(data):
    for name, proj in data.iteritems():
        if 'start_cmd' not in proj:
            if not ignore_err:
                log('a start command is not defined for project %s' % name)
            return False
        if 'teardown_cmd' not in proj:
            if not ignore_err:
                log('a teardown command is not defined for project %s' % name)
            return False
        if 'root' not in proj:
            if not ignore_err:
                log('a root directory is not defined for project %s' % name)
            return False
    return True

RC_NOT_FOUND_MSG = \
'''cannot continue please make an rcfile
    you can make an rcfile by adding a project using `sw add` command.
    Alternatively, you can manually create a ~/.sworkrc. To do so please see the
    output of `sw --help-config`
'''

def loadrc(ignore_err=False):
    if not os.path.exists(rcfile):
        if not ignore_err:
            log('no rc file exists looked at: %s' % rcfile)
            log(RC_NOT_FOUND_MSG)
        return False
    f = open(rcfile, 'r')
    try:
        data = json_load(f)
    finally:
        f.close()
    if validaterc(data):
        return data
    return False

def saverc(rc):
    if validaterc(rc):
        with open(rcfile, 'w') as f:
            json.dump(rc, f, indent=4)
        return True
    return False

def addproj(name, root, start, end):
    rc = loadrc(True)
    if rc == False: rc = dict()
    rc.update({name:{'root':root, 'start_cmd':start, 'teardown_cmd':end}})
    return saverc(rc)

def rmproj(name):
    rc = loadrc(True)
    if rc == False: rc = dict()
    del rc[name]
    return saverc(rc)

def pushproj(name):
    cur = open(getfile('cur'), 'w')
    cur.write(name)
    cur.close()

def popproj():
    cur = open(getfile('cur'), 'r')
    name = cur.read().strip()
    cur.close()
    open(getfile('cur'), 'w').close()

    if not name: return
    rc = loadrc()
    if name not in rc: return
    proj = rc[name]
    output('cd %s' % (proj['root']))
    output(proj['teardown_cmd'])

