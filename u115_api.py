#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import time
import random
import string
import os
from urllib import urlencode
from urllib import quote
import MultipartPostHandler, urllib2, cookielib
from hashlib import sha1

from http_request import http_request
import mail_pop3

BT_API_URL = 'http://btapi.115.com'
BASE_URL = 'http://115.com'
PASSPORT_URL = 'http://passport.115.com'
LOGIN_URL = PASSPORT_URL + '/?ct=login&ac=ajax&is_ssl=1'

class u115_api:

    def __init__(self):
        self.http = http_request()

    def setcookie(self, cookie):
        self.http.cookie = cookie

    def login(self, username, password):
        #这混蛋115也是存密码明文
        #好吧,我们也来生成一个key
        key = string.join(random.sample(['a','b','c','d','e','f','0','1','2','3','4','5','6','7','8','9'], 13)).replace(' ', '')
        vcode = key.upper()
        password = sha1(sha1(sha1(password).hexdigest() + sha1(username).hexdigest()).hexdigest() + vcode).hexdigest()
        data = urlencode({'login[ssoent]' : 'B1', 'login[version]' : '2.0', 'login[ssoext]': key, 'login[ssoln]':username, 'login[ssopw]':password, 'login[ssovcode]':key, 'login[safe]':'1', 'login[time]':'1', 'login[safe_login]':'0', 'login[goto]':'http://www.115.com/'})
        resp, ret = self.http.post(LOGIN_URL, data, setcookie = True)
        if not resp['status'] == 200:
            print '115登陆失败:请求失败'
            return
        ret = json.loads(ret)
        if ret.has_key('error_msg'):
            print '115登陆失败:%s' % ret['err_msg'].encode('utf-8')
        else:
            print '115登陆成功'
            self.get_uid()

    def siginup(self, email, email_pwd, passwd):
        get_url = BASE_URL
        resp, ret = self.http.get(get_url)
        if not resp['status'] == 200:
            print 'get_sign失败:请求失败'
            return
        #从页面中获取几个参数
        reg = re.compile('\\[\'auth\'\\] = \'(\S+)\'')
        ids = re.findall(reg, ret)
        if len(ids) == 0:
            print '获取atuh失败:似乎没有找到atuh'
            return
        auth = quote(str(ids[0]))
        #从页面中获取几个参数
        reg = re.compile('bridgeUrl:"(\S+)"')
        ids = re.findall(reg, ret)
        if len(ids) == 0:
            print '获取bridgeurl失败:似乎没有找到bridgeurl'
            return
        bridgeurl = str(ids[0])
        #获取验证码
        resp, ret = self.http.get(PASSPORT_URL + '/?ct=securimage&ac=email', setcookie = True)
        if not resp['status'] == 200:
            print '获取验证码失败:请求失败'
            return
        file = open('code.png', 'wb')
        file.write(ret)
        file.close()

        vocode = raw_input("请输入code.png验证码:\n")

        bridgeurl = bridgeurl + '?ajax_cb_key=bridge_bridge_1388735845341'
        resp, ret = self.http.get(bridgeurl)
        if not resp['status'] == 200:
            print '注册失败:请求失败'
            return

        postdata = 'type=email&email=%s&passwd=%s&code=%s&auth=%s' % (email, passwd, vocode, auth)
        print bridgeurl
        resp, ret = self.http.post(uri = PASSPORT_URL + '/?ct=register&ac=create&is_ajax=1&mini=n&goto=http%3A%2F%2F115.com', postdata = postdata, referer = bridgeurl)
        if not resp['status'] == 200:
            print '注册失败:请求失败'
            return

        ret = json.loads(ret)
        if ret['state'] == True:
            print '注册成功:等待验证'
        else:
            if ret.has_key('err_msg'):
                print postdata
                print '注册失败:%s' % ret['err_msg'].encode('utf-8')
                return
        #准备收取邮件
        time.sleep(2)
        trytime = 3
        while(trytime>0):
            ret = mail_pop3.check_mail_url(email, email_pwd)
            if ret == None:
                print '3秒后重试...'
                trytime = trytime - 1
                time.sleep(3)
            else:
                break

        resp, ret = self.http.get(ret)
        if not resp['status'] == 200:
            print '访问激活地址失败:请求失败'
            return
        print '注册成功: 帐号:%s 密码:%s' % (email, passwd)

    def get_uid(self):
        resp, ret = self.http.get(BASE_URL)
        if not resp['status'] == 200:
            print '获取用户id失败:请求失败'
            return
        reg = re.compile('USER_ID = \'(\d+)')
        ids = re.findall(reg, ret)
        if len(ids) == 0:
            print '获取用户id失败:似乎没有找到id'
            return
        self.uid = str(ids[0])

    def get_sign(self):
        get_url = BASE_URL + '/?ct=offline&ac=space&_=' + str(time.time())
        resp, ret = self.http.get(get_url)
        if not resp['status'] == 200:
            print 'get_sign失败:请求失败'
            return
        ret = json.loads(ret)
        if ret.has_key('error_msg'):
            print 'get_sign失败:%s' % ret['error_msg'].encode('utf-8')
            return
        else:
            self.sign = str(ret['sign'])
            self.time = str(ret['time'])

    def get_bt_task_list(self):
        '''
        "status": -2完成 0转移
        "status": 4,正在找资源
        "percentDone": 7.57,完成率
        {
    {
        "show": "all",
        "torrents": [
            {
                "info_hash": "2810f36ee5c62fb96d0aa606bcb51758b9ddd244",
                "add_time": 1380994493,
                "percentDone": 100,
                "size": 226228065,
                "peers": 0,
                "rateDownload": 0,
                "torrent_name": "[KTXP][Mushi_Bugyou][26][720P][BIG5].mp4",
                "last_update": 1380898960,
                "status": -2,
                "move": 1,
                "file_id": "91823621349291204",下载完成后
                "left_time": 0
            },
            {
                "info_hash": "0b77985699f34fa2dacfa6ce0662fe0624c4fb14",
        '''
        self.get_sign()

        post_url = BT_API_URL +  '/task/list'
        torrents = []
        current_page = 1
        page_count = 1
        while current_page <= page_count:
            post_data = 'page=%d&uid=%s&sign=%s&time=%s' % (current_page, self.uid, self.sign, self.time)
            resp, ret = self.http.post(post_url, post_data)
            if not resp['status'] == 200:
                self.torrents = None
                print '获取列表失败:请求失败'
                return
            ret = json.loads(ret)
            if ret.has_key('page_count'):
                page_count = ret['page_count']
            if ret.has_key('torrents'):
                torrents.extend(ret['torrents'])
            current_page += 1
        self.torrents = torrents

    def ret_current_bt_task_count(self, refresh = True):
        count = 0
        if refresh:
            self.get_bt_task_list()
        if self.torrents == None:
            return 999
        for i in range(0, len(self.torrents)):
            if self.torrents[i]['status'] == -1:
                continue
            #if self.torrents[i]['file_id'] == None:
            count = count + 1
        return count


    def upload_torrent(self, torrent_file_path):
        '''
            path:种子本地路径;
            torrent_oid:原种子id;
            sign:从115页面获取;
            uid:从115页面获取'
        '''
        self.get_sign()

        torrent_file_name = os.path.basename(torrent_file_path)
        #模拟flash提交插件把种子传上去
        post_url = BT_API_URL +  '/task/torrent'
        params = { 'Filename' : torrent_file_name, 'time' : self.time, 'sign' : self.sign, 'uid' : self.uid, 'torrent' : open(torrent_file_path, 'rb'), 'Upload' : 'Submit Query'}
        cookies = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies), MultipartPostHandler.MultipartPostHandler)
        opener.addheaders = [('User-Agent', 'Shockwave Flash'),
                       ('Accept', 'text/*'),
                       ('Cookie', self.http.cookie)]
        try:
            ret = json.loads(opener.open(post_url, params, timeout = 66).read())
        except Exception, e:
            print '种子文件上传失败:请求失败'
            return False
        if ret.has_key('error_msg'):
            errstr = ret['error_msg'].encode('utf-8')
            if errstr.find('此种子已经在当前任务队列中') > -1:
                print '种子取消提交:%s' % errstr
                return True
            print '种子文件上传失败:%s' %  ret['error_msg'].encode('utf-8')
            return False
        if not ret.has_key('file_count') or ret['file_count'] == 0:
            print '种子文件内容为空!'
            return False

        #模拟选择文件开始任务
        post_url = BT_API_URL +  '/task/start'
        wanted = '0'
        for i in range(1, ret['file_count']):
            wanted = wanted + '%2C' + str(i)
        #115有个小bug,文件名包含'会出问题
        m = {'savepath' : ret['torrent_name'].encode('utf-8').replace('\'', '')}
        s = urlencode(m)
        post_data = 'info_hash=%s&wanted=%s&%s&uid=%s&sign=%s&time=%s' % (ret['info_hash'], wanted, s, self.uid, self.sign, self.time)
        resp, ret = self.http.post(post_url, post_data)
        if not resp['status'] == 200:
            print '任务开始失败:请求失败'
            return False
        ret = json.loads(ret)
        if ret.has_key('error_msg'):
            #服务器返回失败
            errstr = ret['error_msg'].encode('utf-8')
            #if errstr.find('繁忙') == -1:
                #除这种情况之外都应该是失败了
            print '任务开始失败:%s' % errstr
            return False
        print '任务 torrent=%s 提交成功' % torrent_file_name
        return True
        #完成添加操作,将ret['info_hash'] ret['name']更新入数据库
        #m = {'torrent_info_hash' : ret['info_hash'], 'torrent_name' : ret['name']}
        #s = urlencode(m)
        #get_url = config.MY_DATAQUERY_URL + '&type=update_info_hash&' + s + '&ori_torrent_id=' + torrent_oid + "&"
        #h.request(get_url)

    def print_bt_task_info(self):
        self.get_bt_task_list()
        total_rateDownload = 0
        for i in range(0, len(self.torrents)):
            if self.torrents[i]['status'] == -1:
                continue
            if self.torrents[i]['file_id'] == None:
                print '任务:%120s  进度:%8s  速度:%10dKB/s  种子:%5s  体积: %5.2f    散列值:%40s' % (self.torrents[i]['torrent_name'].encode('utf-8'), str(self.torrents[i]['percentDone']), self.torrents[i]['rateDownload']/1024.0, str(self.torrents[i]['peers']), self.torrents[i]['size']/1024.0/1024.0/1024.0, self.torrents[i]['info_hash'].encode('utf-8'))
                total_rateDownload += self.torrents[i]['rateDownload']/1024.0
        print '---------------------------------总速度:%5.2f MB/s' % (total_rateDownload/1024.0)

    def auto_make_share_link(self, refresh = True):
     #自动将完成任务生成网盘礼包
        if refresh:
            self.get_bt_task_list()
        else:
            self.get_sign()
        if self.torrents == None:
            print 'torrents == None'
            return
        for i in range(0, len(self.torrents)):
            if self.torrents[i]['status'] == -1:
                post_url = BT_API_URL + '/task/del'
                post_data = 'hash%%5B0%%5D=%s&uid=%s&sign=%s&time=%s' % (self.torrents[i]['info_hash'].encode('utf-8'), self.uid, self.sign, self.time)
                self.http.post(post_url, post_data)
                print '删除失败的任务:%s' % self.torrents[i]['info_hash']
                continue
            #if self.torrents[i]['file_id'] != None and (self.torrents[i]['status'] == -2 or (self.torrents[i]['status'] == 0 and self.torrents[i]['percentDone'] == 100)):
            if self.torrents[i]['file_id'] != None and self.torrents[i]['status'] == -2:
                cid = str(self.torrents[i]['file_id'])
                torrent_name = '%s' % self.torrents[i]['torrent_name'].encode('utf-8')
                get_url = 'http://web.api.115.com/category/get?aid=1&cid=%s' % cid
                resp, ret = self.http.get(get_url)#sometime has bom
                if not resp['status'] == 200:
                    print '分享失败:请求失败'
                    return
                if ret.find('pick_code') < 0:
                    #此时无bom
                    print '分享失败:未找到pick_code'
                    continue
                #此时有bom.....................
                ret = ret[3:]
                ret = json.loads(ret)
                pick_code = ret['pick_code']
                #创建礼包
                post_url = BASE_URL + '/?ct=filegift&ac=create'
                post_data = 'pickcodes%%5B%%5D=%s' % pick_code
                resp, ret = self.http.post(post_url, post_data)
                if not resp['status'] == 200:
                    self.torrents = None
                    print '创建礼包失败:请求失败'
                    return
                ret = json.loads(ret)
                gift_code = ret['gift_code']
                #保存礼包名字
                post_url = BASE_URL + '/?ct=filegift&ac=update_remark'
                m = {'remark' : torrent_name}
                s = urlencode(m)
                post_data = 'gift_code=%s&%s' % (gift_code, s)
                resp, ret = self.http.post(post_url, post_data)
                if not resp['status'] == 200:
                    self.torrents = None
                    print '保存礼包名字失败:请求失败'
                    return
                ret = json.loads(ret)
                print '生成礼包成功:Code=%s Hash=%s Name=%s' % (gift_code.encode('utf-8'), self.torrents[i]['info_hash'].encode('utf-8'), torrent_name)
                #将gift_code更新入数据库中
                #get_url = config.MY_DATAQUERY_URL + '&type=update_gift_code' + '&gift_code=' + gift_code + '&torrent_info_hash=' + self.torrents[i]['info_hash']
                #115从完成列表中删除
                post_url = BT_API_URL + '/task/del'
                post_data = 'hash%%5B0%%5D=%s&uid=%s&sign=%s&time=%s' % (self.torrents[i]['info_hash'].encode('utf-8'), self.uid, self.sign, self.time)
                self.http.post(post_url, post_data)
                print '删除完成任务:Code=%s Hash=%s Name=%s' % (gift_code.encode('utf-8'), self.torrents[i]['info_hash'].encode('utf-8'), torrent_name)

if __name__ == "__main__":
     u115 = u115_api()
     #u115.login('131000000000', '123456')
     #print u115.ret_current_bt_task_count()
     #u115.print_bt_task_info()
     #u115.upload_torrent('D:\\code\\python\\NexusPHPSpider\\torrents\\1.torrent')
     #u115.auto_make_share_link()