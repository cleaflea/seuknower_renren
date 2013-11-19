#-*-coding:utf-8-*-

import requests
import json
import re
import random
from pyquery import PyQuery
from encrypt import encryptString
import os
import redis

class RenRen:

    def __init__(self, email=None, pwd=None):
        self.session = requests.Session()
        self.token = {}

        if email and pwd:
            self.login(email, pwd)

    def request(self, url, method, data={}):
        if data:
            data.update(self.token)

        if method == 'get':
            return self.session.get(url, data=data)
        elif method == 'post':
            return self.session.post(url, data=data)

    def get(self, url, data={}):
        return self.request(url, 'get', data)

    def post(self, url, data={}):
        return self.request(url, 'post', data)

    def getEncryptKey(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        return r.json()

    def getShowCaptcha(self, email=None):
        r = self.post('http://www.renren.com/ajax/ShowCaptcha', data={'email': email})
        return r.json()

    def getICode(self, fn):
        r = self.get("http://icode.renren.com/getcode.do?t=web_login&rnd=%s" % random.random())
        if r.status_code == 200 and r.raw.headers['content-type'] == 'image/jpeg':
            with open(fn, 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            print "get icode failure"

    def getToken(self, html=''):
        p = re.compile("get_check:'(.*)',get_check_x:'(.*)',env")

        if not html:
            r = self.get('http://www.renren.com')
            html = r.text

        result = p.search(html)
        self.token = {
            'requestToken': result.group(1),
            '_rtk': result.group(2)
        }

    def login(self, email, pwd):
        key = self.getEncryptKey()
        # key = self.handleError()

        if self.getShowCaptcha(email) == 1:
            fn = 'icode.%s.jpg' % os.getpid()
            self.getICode(fn)
            print "Please input the code in file '%s':" % fn
            icode = raw_input().strip()
            os.remove(fn)
        else:
            icode = ''

        if key[u'isEncrypt'] == False:
            print 'false'
            data = {
                'email': email,
                'origURL': 'http://www.renren.com/home',
                'icode': icode,
                'domain': 'renren.com',
                'key_id': 1,
                'captcha_type': 'web_login',
                'password': pwd
            }
        else:
            print 'true'
            data = {
                'email': email,
                'origURL': 'http://www.renren.com/home',
                'icode': icode,
                'domain': 'renren.com',
                'key_id': 1,
                'captcha_type': 'web_login',
                'password': encryptString(key['e'], key['n'], pwd),
                'rkey': key['rkey']
            }
        print "login data: %s" % data
        url = 'http://www.renren.com/ajaxLogin/login?1=1&uniqueTimestamp=%f' % random.random()
        r = self.post(url, data)
        result = r.json()
        if result['code']:
            print 'login successfully'
            self.email = email
            r = self.get(result['homeUrl'])
            self.getToken(r.text)
        else:
            print 'login error', r.text

    def handleError(self):
        r = requests.get('http://login.renren.com/ajax/getEncryptKey')
        result = r.json()
        finalresult = {}
        if result[u'isEncrypt'] == False:
            r = redis.Redis(host='localhost', port=6379, db=0)
            finalresult = r.get('seuknower_encrypt')
            # finalresult[u'isEncrypt'] = True
        else:
            finalresult = result
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.set('seuknower_encrypt', result)

        return finalresult

    def _loginByCookie(self, cookie_str):
        cookie_dict = dict([v.split('=', 1) for v in cookie_str.strip().split(';')])
        self.session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        self.getToken()

    def getNotifications(self):
        url = 'http://notify.renren.com/rmessage/get?getbybigtype=1&bigtype=1&limit=50&begin=0&view=17'
        r = self.get(url)
        try:
            result = json.loads(r.text, strict=False)
        except Exception, e:
            print 'error', e
            result = []
        return result

    def removeNotification(self, notify_id):
        self.get('http://notify.renren.com/rmessage/remove?nl=' + str(notify_id))

    # 评论状态
    def addStatusComment(self, data):
        url = 'http://status.renren.com/feedcommentreply.do'

        payloads = {
            't': 3,
            'rpLayer': 0,
            'source': data['source_id'],
            'owner': data['owner_id'],
            'c': data['message']
        }

        if data.get('reply_id', None):
            payloads.update({
                'rpLayer': 1,
                'replyTo': data['author_id'],
                'replyName': data['author_name'],
                'secondaryReplyId': data['reply_id'],
                'c': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message'])
            })

        return self.sendComment(url, payloads)

    # 回复相册
    def addAlbumComment(self, data):
        url = 'http://photo.renren.com/photo/%d/album-%d/comment' % (data['owner_id'], data['source_id'])

        payloads = {
            'id': data['source_id'],
            'only_to_me' : 'false',
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment' : 'true',
            'owner' : data['owner_id'],
            'replyCommentId' : data['reply_id'],
            'to' : data['author_id']
        }

        return self.sendComment(url, payloads)

    def addPhotoComment(self, data):
        url = 'http://photo.renren.com/photo/%d/photo-%d/comment' % (data['owner_id'], data['source_id'])

        if 'author_name' in data:
            body = '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
        else:
            body = data['message']

        payloads = {
            'guestName': '东大通',
            'feedComment' : 'true',
            'body': body,
            'owner' : data['owner_id'],
            'realWhisper':'false',
            'replyCommentId' : data.get('reply_id', 0),
            'to' : data.get('author_id', 0)
        }

        return self.sendComment(url, payloads)

    # 回复日志
    def addBlogComment(self, data):
        url = 'http://blog.renren.com/PostComment.do'

        payloads = {
            'body': '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
            'feedComment': 'true',
            'guestName': '东大通',
            'id' : data['source_id'],
            'only_to_me': 0,
            'owner': data['owner_id'],
            'replyCommentId': data['reply_id'],
            'to': data['author_id']
        }

        return self.sendComment(url, payloads)

    # 回复分享
    def addShareComment(self, data):
        url = 'http://share.renren.com/share/addComment.do'

        if data.get('reply_id', None):
            body = '回复%s：%s' % (data['author_name'].encode('utf-8'), data['message']),
        else:
            body = data['message']

        payloads = {
            'comment': body,
            'shareId' : data['source_id'],
            'shareOwner': data['owner_id'],
            'replyToCommentId': data.get('reply_id', 0),
            'repetNo' : data.get('author_id', 0)
        }

        return self.sendComment(url, payloads)

    # 回复留言
    def addGossip(self, data):
        url = 'http://gossip.renren.com/gossip.do'

        payloads = {
            'id': data['owner_id'],
            'only_to_me': 1,
            'mode': 'conversation',
            'cc': data['author_id'],
            'body': data['message'],
            'ref':'http://gossip.renren.com/getgossiplist.do'
        }

        return self.sendComment(url, payloads)

    def sendComment(self, url, payloads):
        r = self.post(url, payloads)
        r.raise_for_status()
        try:
            return r.json()
        except:
            return { 'code': 0 }

    def addComment(self, data):
        return {
            'status': self.addStatusComment,
            'album' : self.addAlbumComment,
            'photo' : self.addPhotoComment,
            'blog'  : self.addBlogComment,
            'share' : self.addShareComment,
            'gossip': self.addGossip
        }[data['type']](data)
