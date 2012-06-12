
import select
import os
import sys


def kevent(file):
    ke = select.kevent(file,
        filter=select.KQ_FILTER_VNODE,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        fflags=select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE
    )
    return ke

argvs = sys.argv
argc = len(argvs)
if(argc != 3):
    print 'Usage: python {} filename.'.format(argvs[0])
    quit()
folder = argvs[1]
ssh = argvs[2]
print '{} to {}'.format(folder, ssh)
print 'file update watching...'

dirs = os.walk(folder)
l = []
for root, dirs, files in dirs:
    f = os.open(root, os.O_RDONLY)
    l.append(kevent(f))
    for a in files:
        f = os.open(root + '/' + a, os.O_RDONLY)
        l.append(kevent(f))

kq = select.kqueue()
events = kq.control(l, 0, None)
while True:
    r_events = kq.control(l, 1, None)
    for event in r_events:
        print event
        if event.fflags & select.KQ_NOTE_DELETE or event.fflags & select.KQ_NOTE_WRITE:
            print "file was updated!"
            print 'rsync -av --delete -e ssh {} {}'.format(os.path.join(os.getcwd(), folder), ssh)
            os.system('rsync -av --delete -e ssh {} {}'.format(os.path.join(os.getcwd(), folder), ssh))
