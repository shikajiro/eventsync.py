#!/usr/bin/python
# -*- coding: utf-8 -*-
import select
import os
import subprocess
import re
import json


#ファイルからイベント検知するフラグを取得する
def kevent(file):
    ke = select.kevent(file,
        filter=select.KQ_FILTER_VNODE,
        flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR,
        fflags=select.KQ_NOTE_DELETE | select.KQ_NOTE_WRITE
    )
    return ke


#監視や同期先を記述するEventsyncFile.jsonを取得する。
def getEventsyncFileJson():
    manageFile = open('EventsyncFile.json')
    data = json.load(manageFile)
    return data


#EventsyncFileから監視対象外リストを作成する。
def fixNotWatchingList(manageFile):
    return [os.getcwd() + '/' + n_w for n_w in manageFile['not_watching']]


#EventsyncFileから監視対象外リストを作成する。
def fixExclude(manageFile):
    exclude_str = ''
    for n_s in manageFile['not_sync']:
        exclude_str += '--exclude="' + n_s + '" '
    return exclude_str


#ターゲットが監視対象外か判断する。
def checkIgnore(target, notWatchingList):
    for ignore in notWatchingList:
        c = re.compile(ignore + '*')
        if c.match(target):
            #監視対象外の場合は次に進む
            return True
    return False


#フォルダーの中を監視して、
#変更があった場合していされたrsyncコマンドを実行する
def watching(folder, ssh, manageFile):
    #監視対象から外すリスト
    notWatchingList = fixNotWatchingList(manageFile)
    events = []
    fdList = []

    # ディレクトリ全てを見て、ファイルの識別子を一覧にする。
    for root, dirs, files in os.walk(folder):
        #ディレクトリを監視
        if checkIgnore(root, notWatchingList):
            continue
        else:
            print "check target dir is '{}'".format(root)

        fd = os.open(root, os.O_RDONLY)
        fdList.append(fd)
        events.append(kevent(fd))
        for a in files:
            #ファイルを監視
            fd = os.open(root + '/' + a, os.O_RDONLY)
            fdList.append(fd)
            events.append(kevent(fd))

    #ファイルに変化があるまで監視を続ける。
    while True:
        for event in select.kqueue().control(events, 1, None):
            print event
            if event.fflags & select.KQ_NOTE_DELETE or event.fflags & select.KQ_NOTE_WRITE:
                print "file was updated!"
                #ファイルを転送するために全てのファイルを閉じる
                for fb in fdList:
                    os.close(fb)

                command = 'rsync -av --delete -e ssh {}/ {}'.format(os.getcwd(), ssh)
                exclude = fixExclude(manageFile)
                if exclude:
                    command += " " + exclude
                print ' '
                print 'execute command'
                print command
                print 'command fix.'
                print ' '
                subprocess.call(command, shell=True)
                return

folder = os.getcwd()
manageFile = getEventsyncFileJson()
ssh = manageFile['ssh']
print '{} to {}'.format(folder, ssh)
print 'file update watching...'

#監視をずっと続ける。
#終了する場合は ctrl + C
while True:
    watching(folder, ssh, manageFile)
