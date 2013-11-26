#-*-coding:utf-8-*-

# import MySQLdb
from BeautifulSoup import BeautifulSoup
import urllib
import re
import json
import urllib2, cookielib, urllib
import time
import datetime

import MySQLdb

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def handleEvent(event):
    return 'event' + event

def handleEventLatest():
    # pass
    url = "http://127.0.0.1:8000/seuknower_webservice/event/latest"
    uFile = urllib.urlopen(url)
    eventresult = json.loads(uFile.read())

    if len(eventresult) == 0:
        returnresult = u'暂时没有最新的活动'
    else:
        returnresult = ''.join(eventresult)
        print returnresult
    return returnresult

def handleQuestion(question):
    url = "http://127.0.0.1:8000/seuknower_webservice/qanda/%s" % question.encode('utf-8')
    uFile = urllib.urlopen(url)
    questionlist = json.loads(uFile.read())

    if len(questionlist) == 0:
        returnresult = u'没有找到相关的问题，想知道答案去这里提问吧 http://www.seuknower.com/question'
    else:
        returnresult = ''.join(questionlist)
        print returnresult
    return returnresult

def handleCurriculum(curriculum):
    # return 'curriculum' + curriculum

    studentID = curriculum
    term = '13-14-2'
    a = time.localtime()
    # weekday = int(time.strftime("%w", a))+1
    # weekday = str(weekday)
    weekday = time.strftime("%w", a)

    uFile = urllib.urlopen("http://127.0.0.1:8000/seuknower_webservice/curriculums/%s/%s/%s" % (studentID, term, weekday))
    jsonresult = uFile.read()

    if jsonresult == '没有找到该学生信息':
        renrenresult = '学号打错了哦'

    else:

        result = json.loads(jsonresult)
        # print result

        if weekday != 0 and weekday != 6:
            morning = result[0]
            afternoon = result[1]
            evening = result[2]

            renrenresultlist = []

            if len(morning) == 0 and len(afternoon) == 0 and len(evening) == 0:
                renrenresult = '今天没课 么么哒'
            else:
                if len(morning) == 0:
                    renrenresultlist.append('早上没课 ')
                else:
                    renrenresultlist.append('早上的课 ')
                    for course in morning:
                        renrenresultlist.append(course + ' ')

                if len(afternoon) == 0:
                    renrenresultlist.append('下午没课 ')
                else:
                    renrenresultlist.append('下午的课 ')
                    for course in afternoon:
                        renrenresultlist.append(course + ' ')

                if len(evening) == 0:
                    renrenresultlist.append('晚上没课 ')
                else:
                    renrenresultlist.append('晚上的课 ')
                    for course in evening:
                        renrenresultlist.append(course + ' ')

                renrenresult = ''.join(renrenresultlist)

        if weekday == 6:
            saturday = result
            if len(saturday) == 0:
                renrenresult = '明天没课 么么哒'
            else:
                renrenresult = ''.join(saturday)

        if weekday == 0:
            sunday = result
            if len(sunday) == 0:
                renrenresult = '明天没课 么么哒'
            else:
                renrenresult = ''.join(sunday)

    print renrenresult
    return renrenresult

def handleCommodity(commodity):
    url = "http://127.0.0.1:8000/seuknower_webservice/market/%s" % commodity.encode('utf-8')
    uFile = urllib.urlopen(url)
    eventresult = json.loads(uFile.read())

    if len(eventresult) == 0:
        returnresult = u'没有找到相关商品，去这里看看有没有什么需要的吧 http://www.seuknower.com/market'
    else:
        returnresult = ''.join(eventresult)
        print returnresult

    return returnresult

def handle(message):
    # print message
    if u'@' in message:
        category = message.split(u'@')[0]
        content = message.split(u'@')[1]

        if category == u'活动':
            print 'event'
            # message = handleEvent(content)
            message = handleEventLatest()
        elif category == u'提问':
            print 'question'
            message = handleQuestion(content)
        elif category == u'查课':
            print 'curriculum'
            message = handleCurriculum(content)
        elif category == u'二手':
            print 'commodity'
            message = handleCommodity(content)
        else:
            message = u'不要调戏我'

    else:
        message = u'格式有误 1提问@问题的内容 2查课@一卡通号 3二手@加想买的东西 活动@活动的标题'

    return message
