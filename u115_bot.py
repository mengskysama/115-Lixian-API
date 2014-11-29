#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import getopt

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from u115_api import u115_api

arg_user = None
arg_pass = None
arg_sleeptime = 120
arg_taskfile = None

def readtask():
    global arg_taskfile
    return open(arg_taskfile).readlines()

def update_task(context):
    #lock
    return open('task.txt', 'w').writelines(context)

def update_task_process(context):
    return open('taskprocess.txt', 'a').write(context + '\n')

def update_task_success(context):
    return open('tasksuccess.txt', 'a').write(context + '\n')

def monitor():
    global arg_pass
    global arg_user
    global arg_sleeptime
    global arg_taskfile

    u115 = u115_api()
    u115.login(arg_user, arg_pass)
    while True:
        try:
            ret, result = u115.auto_make_share_link()
            for res in result:
                update_task_success('http://115.com/lb/%s ---- %s' % (res['Code'], res['Name']))

            task_list = readtask()
            if len(task_list) == 0:
                logging.info('没有任务文件...zZZ'.decode('utf-8'))
            else:
                i = task_list[0]
                task_list.pop(0)
                update_task(task_list)
                if not i.startswith("http"):
                    continue
                update_task_process(i)
                u115.add_http_task(i)
            time.sleep(arg_sleeptime)
        except KeyboardInterrupt:
            break
        except:
            import traceback
            print traceback.print_exc()
            time.sleep(arg_sleeptime * 10)
            u115 = u115_api()
            u115.login(arg_user, arg_pass)

def Usage():
    print '115Bot usage:'
    print '-u, --user: 115 account login user'
    print '-p, --pass: 115 account login pass'
    print '-f, --file: task list file\n'
    print '-h, --help: print help message.'
    print '-v, --version: print script version'

def Version():
    print '115Bot ver 0.1'

def main(argv):
    global arg_pass
    global arg_user
    global arg_sleeptime
    global arg_taskfile

    try:
        opts, args = getopt.getopt(argv[1:], 'u:p:f:v:h', ['user=', 'pass=', 'file=', 'help', 'version'])
    except getopt.GetoptError, err:
        print str(err)
        Usage()
        sys.exit(2)

    for o, a in opts:
        if o in ('-h', '--help'):
            Usage()
            sys.exit(1)
        elif o in ('-v', '--version'):
            Version()
            sys.exit(0)
        elif o in ('-f', '--file'):
            arg_taskfile = a
        elif o in ('-u', '--user'):
            arg_user = a
        elif o in ('-p', '--pass'):
            arg_pass = a
        else:
            print 'unhandled option'
            sys.exit(1)

    if arg_taskfile is None:
        print 'missing arg -f'
        sys.exit(2)
    if arg_user is None:
        print 'missing arg -u'
        sys.exit(2)
    if arg_pass is None:
        print 'missing arg -p'
        sys.exit(2)
    monitor()

if __name__ == '__main__':
    main(sys.argv)
