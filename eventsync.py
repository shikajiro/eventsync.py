# -*- coding: utf-8 -*-
import select
import os
import sys
import subprocess


def kevent(file):
    ke = select.kevent(file,
        filter=select.KQ_FILTER_VNODE,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        fflags=select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE
    )
    return ke


def watching(folder, ssh):

    dirs = os.walk(folder)

    fileList = []
    fbs = []

    # ディレクトリ全てを見て、ファイルの識別子を一覧にする。
    for root, dirs, files in dirs:
        f = os.open(root, os.O_RDONLY)
        fbs.append(f)
        fileList.append(kevent(f))
        for a in files:
            f = os.open(root + '/' + a, os.O_RDONLY)
            fbs.append(f)
            fileList.append(kevent(f))

    kq = select.kqueue()
    # events = kq.control(fileList, 0, None)
    is_loop = True
    while is_loop:
        r_events = kq.control(fileList, 1, None)
        for event in r_events:
            print event
            if event.fflags & select.KQ_NOTE_DELETE or event.fflags & select.KQ_NOTE_WRITE:
                print "file was updated!"
                #ファイルを転送するために全てのファイルを閉じる
                for fb in fbs:
                    os.close(fb)
                command = 'rsync -av --delete -e ssh {} {}'.format(os.path.join(os.getcwd(), folder), ssh)
                print command
                subprocess.call(command, shell=True)
                is_loop = False

argvs = sys.argv
argc = len(argvs)
if(argc != 3):
    print 'Usage: python {} filename.'.format(argvs[0])
    quit()
folder = argvs[1]
ssh = argvs[2]
print '{} to {}'.format(folder, ssh)
print 'file update watching...'

while True:
    watching(folder, ssh)
