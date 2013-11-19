#-*-coding:utf-8-*-

import re
import sys
import redis
from renrenapi import RenRen
# from renren import RenRen
from accounts import accounts
from ntype import NTYPES
from handlemessage import handle

self_match_pattern = re.compile('@东大通(\(601792587\))?')
REDIS_HOST = 'localhost'

def getBots(accounts):
    # 当使用python main.py启动的时候，也就是第一次启动的时候要初始登录
    if 'main.py' in sys.argv[0]:
        print 'condition1'
        bots = []
        for account in accounts:
            bot = RenRen()
            bot.login(account[0], account[1])
            print bot.email, 'login'
            bots.append(bot)
        return bots
    # 之后循环进来登录的，就从cookie里面拿登录信息，而不要重新提交登录表单，貌似经常重复提交会有问题
    else:
        print 'condition2'
        r = redis.Redis(REDIS_HOST)
        cookies = r.get('xiaohuangji_cookies')
        bot = RenRen()
        if cookies:
            bot._loginByCookie(cookies)
            bot.email = ''
        else:
            account = accounts[0]
            bot.login(account[0], account[1])
        return [bot] if bot.token else []

bots = getBots(accounts)

# 从一条评论里提取出内容，去掉'回复xx:'和'@小黄鸡'
def extractContent(message):
    content = self_match_pattern.sub('', message)
    content_s = content.split('：', 1)
    if len(content_s) == 1:
        content_s = content.split(': ', 1)
    if len(content_s) == 1:
        content_s = content.split(':', 1)
    content = content_s[-1]
    return content

# 根据通知得到该回复的更详细信息
def getNotiData(bot, data):
    ntype, content = int(data['type']), ''

    payloads = {
        'owner_id': data['owner'],
        'source_id': data['source']
    }

    if ntype == NTYPES['at_in_status'] or ntype == NTYPES['reply_in_status_comment']:
        owner_id, doing_id = data['owner'], data['doing_id']

        payloads['type'] = 'status'

        if ntype == NTYPES['at_in_status'] and data['replied_id'] == data['from']:
            content = self_match_pattern.sub('', data['doing_content'].encode('utf-8'))
        else:
            # 防止在自己状态下@自己的时候有两条评论
            if ntype == NTYPES['at_in_status'] and owner_id == '601621937':
                return None, None
            reply_id = data['replied_id']
            comment = bot.getCommentById(owner_id, doing_id, reply_id)
            if comment:
                payloads.update({
                    'author_id': comment['ownerId'],
                    'author_name': comment['ubname'],
                    'reply_id': reply_id
                })
                content = extractContent(comment['replyContent'].encode('utf-8'))
            else:
                return None, None
    else:
        return None, None

    return payloads, content.strip()


def reply(data):
    # take the first account
    bot = bots[0]

    data, message = getNotiData(bot, data)

    if not data:
        return

    # 不要自问自答
    if '东大通' in data.get('author_name', u'').encode('utf-8'):
        return

    print 'handling comment', data, '\n'

    # data['message'] = questionfilter(message)
    # answer = magic(data, bot)
    # data['message'] = answerfilter(answer)
    # data['message'] = u'明天没课 么么哒'
    data['message'] = handle(message)

    result = bot.addComment(data)

    code = result['code']
    if code == 0:
        return

    if code == 10:
        print 'some server error'
    else:
        raise Exception('Error sending comment by bot %s' % bot.email)
