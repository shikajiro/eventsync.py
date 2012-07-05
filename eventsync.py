# -*- coding: utf-8 -*-
import select
import os
import sys
import subprocess


#ファイルからイベント検知するフラグを取得する
def kevent(file):
    ke = select.kevent(file,
        filter=select.KQ_FILTER_VNODE,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        fflags=select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE
    )
    return ke


#フォルダーの中を監視して、
#変更があった場合していされたrsyncコマンドを実行する
def watching(folder, ssh):
    events = []
    fdList = []

    # ディレクトリ全てを見て、ファイルの識別子を一覧にする。
    for root, dirs, files in os.walk(folder):
        #ディレクトリを監視
        fd = os.open(root, os.O_RDONLY)
        fdList.append(fd)
        events.append(kevent(fd))
        for a in files:
            #ファイルを監視
            fd = os.open(root + '/' + a, os.O_RDONLY)
            fdList.append(fd)
            events.append(kevent(fd))

    is_loop = True
    while is_loop:
        for event in select.kqueue().control(events, 1, None):
            print event
            if event.fflags & select.KQ_NOTE_DELETE or event.fflags & select.KQ_NOTE_WRITE:
                print "file was updated!"
                #ファイルを転送するために全てのファイルを閉じる
                (os.close(fb) for fb in fdList)

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

#監視をずっと続ける。
#終了する場合は ctrl + C
while True:
    watching(folder, ssh)
