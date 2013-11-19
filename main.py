#-*-coding:utf-8-*-

from ntype import NTYPES
from redis import Redis
from rq import Queue
import sys
import time
from controller import bots, reply

redis_conn = Redis()
q = Queue(connection=redis_conn)

def handle(bot, notification):

    print time.strftime('%Y-%m-%d %I:%M:%S', time.localtime(time.time())), 'got notification'
    if int(notification['type']) in NTYPES.values():
        # 进入消息队列
        q.enqueue(reply, notification)
        # print 'start to reply!!!!!!!!!!!!!!!!'
        # reply(notification)

# 得到人人上的通知，处理之
def process(bot, just_clear=False):
    # print 'process'
    notifications = bot.getNotifications()
    # print notifications

    for notification in notifications:

        print notification

        # notify_id = notification['notify_id']
        notify_id = notification[u'notify_id']
        print notify_id

        bot.removeNotification(notify_id)

        # 如果已经处理过了, 或在执行清空消息脚本
        if redis_conn.get(notify_id) or just_clear:
            print 'clear' if just_clear else 'get duplicate notification', notification
            return

        try:
            redis_conn.set(notify_id, True)
            handle(bot, notification)
            redis_conn.incr('comment_count')
        except Exception, e:
            print e

        print ''

def main():
    while True:
        try:
            map(process, bots)
        except KeyboardInterrupt:
            sys.exit()
        except Exception, e:
            print e

if __name__ == '__main__':
    main()
