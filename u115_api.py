#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import time
import random
import string
import os
import logging

from hashlib import sha1
from http_request import http_request

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

BT_API_URL = 'http://btapi.115.com'
UPLOAD_URL = 'http://upload.115.com'
BASE_URL = 'http://115.com'
PASSPORT_URL = 'http://passport.115.com'
WEB_API_URL = 'http://web.api.115.com'
LOGIN_URL = PASSPORT_URL + '/?ct=login&ac=ajax&is_ssl=1'


class u115_api:

    def __init__(self):
        self.http = http_request()
        self.torrents = None
        self.sign = None
        self.time = None
        self.uid = 0

    def setcookie(self, cookie):
        self.http.cookie = cookie

    def login(self, username, password):
        #这混蛋115也是存密码明文
        #好吧,我们也来生成一个key
        key = string.join(random.sample(['a', 'b', 'c', 'd', 'e', 'f', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                                        , 13)).replace(' ', '')
        vcode = key.upper()
        password = sha1(sha1(sha1(password).hexdigest() + sha1(username).hexdigest()).hexdigest() + vcode).hexdigest()
        data = {'login[ssoent]': 'B1',
                'login[version]': '2.0',
                'login[ssoext]': key,
                'login[ssoln]': username,
                'login[ssopw]': password,
                'login[ssovcode]': key,
                'login[safe]': '1',
                'login[time]': '1',
                'login[safe_login]': '0',
                'login[goto]': 'http://www.115.com/'}
        resp, ret = self.http.post(LOGIN_URL, data)
        if not resp['status'] == 200:
            logging.error('115登陆失败:请求失败'.decode('utf-8'))
            return False
        ret = json.loads(ret)
        if 'err_msg' in ret:
            logging.error(('115登陆失败:%s' % ret['err_msg'].encode('utf-8')).decode('utf-8'))
            return False
        else:
            logging.info('115登陆成功'.decode('utf-8'))
            self.get_uid()
            return True

    def siginup(self, email, email_pwd, passwd):
        """已经变更为手机注册"""

    def get_uid(self):
        resp, ret = self.http.get(BASE_URL)
        if not resp['status'] == 200:
            logging.error('获取用户id失败:请求失败'.decode('utf-8'))
            return
        reg = re.compile('USER_ID = \'(\d+)')
        ids = re.findall(reg, ret)
        if len(ids) == 0:
            logging.error('获取用户id失败:似乎没有找到id'.decode('utf-8'))
            return
        self.uid = str(ids[0])
        logging.info(('用户id:%s' % self.uid).decode('utf-8'))

    def get_sign(self):
        get_url = BASE_URL + '/?ct=offline&ac=space&_=' + str(time.time())
        #print get_url
        resp, ret = self.http.get(get_url)
        if not resp['status'] == 200:
            logging.error('get_sign失败:请求失败'.decode('utf-8'))
            return
        ret = json.loads(ret)
        if ret.has_key('error_msg'):
            logging.error(('get_sign失败:%s' % ret['error_msg'].encode('utf-8')).decode('utf-8'))
            return
        else:
            self.sign = str(ret['sign'])
            self.time = str(ret['time'])

    def get_bt_task_list(self):
        '''
        "status": 2完成
        "status": 4,正在找资源，-1失败
        "percentDone": 7.57,完成率
        '''
        self.get_sign()

        post_url = BASE_URL + '/lixian/?ct=lixian&ac=task_lists'
        torrents = []
        current_page = 1
        page_count = 1
        while current_page <= page_count:
            data = {'page': current_page, 'uid': self.uid, 'sign': self.sign, 'time' : self.time}
            resp, ret = self.http.post(post_url, data)
            if not resp['status'] == 200:
                self.torrents = None
                logging.error('获取列表失败:请求失败'.decode('utf-8'))
                return
            #print ret
            ret = json.loads(ret)
            if 'page_count' in ret:
                page_count = ret['page_count']
            if 'tasks' in ret and ret['tasks'] is not None:
                torrents.extend(ret['tasks'])
            current_page += 1
        self.torrents = torrents

    def ret_current_bt_task_count(self, refresh = True):
        #非完成状态都算在活动内
        count = 0
        if refresh:
            self.get_bt_task_list()
        if self.torrents is None:
            return 999
        for i in range(0, len(self.torrents)):
            if self.torrents[i]['status'] == 2:
                continue
            #if self.torrents[i]['file_id'] == None:
            count += 1
        return count


    def add_torrent_task(self, torrent_file_path):
        '''
            这个接口简直屌炸天了有没有................
        '''
        #step.0
        #更新sign
        self.get_sign()
        #step.1
        #得到CID
        resp, ret = self.http.get(BASE_URL + '/?ct=lixian&ac=get_id&torrent=1&_=' + self.time)
        ret = json.loads(ret)
        cid = ret['cid']
        #print cid
        #step.2
        #得到上传地址
        resp, ret = self.http.get(BASE_URL + '/?tab=offline&mode=wangpan')
        reg = re.compile('upload\?(\S+?)"')
        ids = re.findall(reg, ret)
        if ids == 0:
            logging.error('没有找到上传入口'.decode('utf-8'))
            return False
        url = 'http://upload.115.com/upload?' + ids[0]
        #step.3
        #模拟flash提交插件把种子传上去
        torrent_file_name = os.path.basename(torrent_file_path)
        post_url = url
        params = {'Filename': (None, torrent_file_name), 'target': (None, 'U_1_' + cid),
                  'Filedata': (torrent_file_name, open(torrent_file_path, 'rb'), 'application/octet-stream'),
                  'Upload': (None, 'Submit Query')}
        resp, ret = self.http.upload(post_url, files=params)
        #{"state":true,"data":{"cid":138235783244134093,"aid":1,"file_name":"ea97783ca86b4ec4b409e8c766e3feff8848c7d7.torrent","file_ptime":1411607247,"file_status":1,"file_id":"348892672322418456","file_size":21309,"pick_code":"ewu87sytxapt7zwyi","sp":1}}
        ret = json.loads(ret)
        if 'state' is False:
            logging.error(('上传种子step.3出错 %s!' % str(ret)).decode('utf-8'))
            return False
        #step.4
        #还要传一个地方..
        url = WEB_API_URL + '/files/file'
        data = {'file_id': ret['data']['file_id']}
        resp, ret = self.http.post(url, data)
        ret = json.loads(ret)
        print ret
        #返回{"data":[{"file_id":"348892672322418456","file_name":"ea97783ca86b4ec4b409e8c766e3feff8848c7d7.torrent","pick_code":"ewu87sytxapt7zwyi","sha1":"C72830D1D4C559E553A1A1074A8FC33D3D1F1336"}],"state":true,"error":"","errNo":0}
        if ret['state'] is False:
            logging.error(('上传种子step.4出错 %s!' % str(ret)).decode('utf-8'))
            return False
        #step.5
        #获取服务器解析结果
        post_url = BASE_URL + '/lixian/?ct=lixian&ac=torrent'
        data = {'pickcode': ret['data'][0]['pick_code'],
                'sha1': ret['data'][0]['sha1'],
                'uid': self.uid,
                'sign': self.sign,
                'time': self.time}
        resp, ret = self.http.post(post_url, data)
        ret = json.loads(ret)
        #fail
        #{"file_size":0,"torrent_name":"","file_count":0,"info_hash":"","torrent_filelist_web":null,"state":false,"error_msg":""}
        #success
        #{"file_size":2201795620,"torrent_name":"[KTXP][RE Hamatora][01-12][BIG5][720p][MP4]","file_count":23,"info_hash":"d62d53175e0367a4e99fa464665d11ea1a666de0","torrent_filelist_web":[{"size":192359446,"path":"[KTXP][RE Hamatora][01][BIG5][720p][MP4].mp4","wanted":1},{"size":54250,"path":"_____padding_file_0_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":207823616,"path":"[KTXP][RE Hamatora][02][BIG5][720p][MP4].mp4","wanted":1},{"size":318720,"path":"_____padding_file_1_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":211146572,"path":"[KTXP][RE Hamatora][03][BIG5][720p][MP4].mp4","wanted":1},{"size":141492,"path":"_____padding_file_2_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":188201661,"path":"[KTXP][RE Hamatora][04][BIG5][720p][MP4].mp4","wanted":1},{"size":17731,"path":"_____padding_file_3_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":179834914,"path":"[KTXP][RE Hamatora][05][BIG5][720p][MP4].mp4","wanted":1},{"size":520158,"path":"_____padding_file_4_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":181628715,"path":"[KTXP][RE Hamatora][06][BIG5][720p][MP4].mp4","wanted":1},{"size":299221,"path":"_____padding_file_5_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":174835936,"path":"[KTXP][RE Hamatora][07][BIG5][720p][MP4].mp4","wanted":1},{"size":276256,"path":"_____padding_file_6_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":173709712,"path":"[KTXP][RE Hamatora][08][BIG5][720p][MP4].mp4","wanted":1},{"size":353904,"path":"_____padding_file_7_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":186998397,"path":"[KTXP][RE Hamatora][09][BIG5][720p][MP4].mp4","wanted":1},{"size":172419,"path":"_____padding_file_8_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":190285300,"path":"[KTXP][RE Hamatora][10][BIG5][720p][MP4].mp4","wanted":1},{"size":31244,"path":"_____padding_file_9_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":155175370,"path":"[KTXP][RE Hamatora][11][BIG5][720p][MP4].mp4","wanted":1},{"size":13878,"path":"_____padding_file_10_if you see this file, please update to BitComet 0.85 or above____","wanted":-1},{"size":157596708,"path":"[KTXP][RE Hamatora][12][BIG5][720p][MP4].mp4","wanted":1}],"state":true}
        if ret['state'] is False:
            logging.error(('上传种子step.5出错 %s!' % str(ret)).decode('utf-8'))
            return False
        #step.6
        #选择需要下载的文件(能下的都下)
        wanted = None
        idx = 0
        for item in ret['torrent_filelist_web']:
            if item['wanted'] != -1:
                if wanted is None:
                    wanted = str(idx)
                else:
                    wanted = wanted + ',' + str(idx)
            idx += 1

        post_url = BASE_URL + '/lixian/?ct=lixian&ac=add_task_bt'
        data = {'info_hash': ret['info_hash'],
                'wanted': wanted,
                #115有个小bug,文件名包含'会出问题
                'savepath': ret['torrent_name'].replace('\'', ''),
                'uid': self.uid,
                'sign': self.sign,
                'time': self.time}
        resp, ret = self.http.post(post_url, data)
        ret = json.loads(ret)
        if 'error_msg' in ret:
            logging.error(ret['error_msg'])
            return False

        logging.info(('任务 torrent=%s 提交成功' % torrent_file_name).decode('utf-8'))
        return True
        #完成添加操作,将ret['info_hash'] ret['name']更新入数据库
        #m = {'torrent_info_hash' : ret['info_hash'], 'torrent_name' : ret['name']}
        #s = urlencode(m)
        #get_url = config.MY_DATAQUERY_URL + '&type=update_info_hash&' + s + '&ori_torrent_id=' + torrent_oid + "&"
        #h.request(get_url)

    def print_bt_task_info(self):
        self.get_bt_task_list()
        total_ratedownload = 0
        for i in range(0, len(self.torrents)):
            if self.torrents[i]['status'] == -1:
                status = '已失败'
            elif self.torrents[i]['status'] == 2:
                status = '已完成'
                if self.torrents[i]['move'] == 0:
                    status = '转储中'
            else:
                status = '下载中'
            if self.torrents[i]['file_id'] is not None:
                print ('任务[%s]:%100s  进度:%8s  速度:%10dKB/s  种子:%5s  体积: %5.2fGB    散列值:%40s' \
                      % (status,
                         self.torrents[i]['name'].encode('utf-8'),
                         str(self.torrents[i]['percentDone']),
                         self.torrents[i]['rateDownload']/1024.0,
                         str(self.torrents[i]['peers']),
                         self.torrents[i]['size']/1024.0/1024.0/1024.0,
                         self.torrents[i]['info_hash'].encode('utf-8'))).decode('utf-8')
                total_ratedownload += self.torrents[i]['rateDownload']/1024.0
        print ('---------------------------------总速度:%5.2f MB/s' % (total_ratedownload/1024.0)).decode('utf-8')

    def add_http_task(self, url):
        self.get_sign()
        post_url = BASE_URL + '/lixian/?ct=lixian&ac=add_task_url'
        post_data = {'url': url.encode('utf-8'),
                     'uid': self.uid,
                     'sign': self.sign,
                     'time': self.time}
        resp, ret = self.http.post(post_url, post_data)
        if not resp['status'] == 200:
            logging.error('任务添加失败:请求失败'.decode('utf-8'))
            return False
        ret = json.loads(ret)
        if ret['state'] is False:
            if 'error_msg' in ret:
                print ret['error_msg']
                return False
            logging.error('任务添加失败'.decode('utf-8'))
            return False
        logging.info(('任务 url=%s 提交成功' % url).decode('utf-8'))
        return True

    def auto_make_share_link(self, refresh=True, delfromlist=True):
    #自动将完成任务生成网盘礼包
        result = []
        if refresh:
            self.get_bt_task_list()
        else:
            self.get_sign()
        if self.torrents is None:
            print 'torrents is None'
            return False, result
        for i in range(0, len(self.torrents)):
            torrent_name = '%s' % self.torrents[i]['name'].encode('utf-8')
            if self.torrents[i]['status'] == -1:
                post_url = BASE_URL + '/lixian/?ct=lixian&ac=task_del'
                post_data = {'hash[0]': self.torrents[i]['info_hash'].encode('utf-8'),
                             'uid': self.uid,
                             'sign': self.sign,
                             'time': self.time}
                self.http.post(post_url, post_data)
                logging.info(('删除失败的任务:%s' % torrent_name).decode('utf-8'))
                continue
            if self.torrents[i]['status'] == 2 \
                    and self.torrents[i]['percentDone'] == 100 \
                    and self.torrents[i]['move'] == 1:

                cid = str(self.torrents[i]['file_id'])
                if cid != '132111574000449453':
                    get_url = 'http://web.api.115.com/category/get?aid=1&cid=%s' % cid
                    resp, ret = self.http.get(get_url)#sometime has bom
                    if not resp['status'] == 200:
                        logging.error('%s 分享失败:请求失败' % torrent_name)
                        continue
                    if ret.find('pick_code') < 0:
                        #此时无bom
                        logging.error('%s 分享失败:未找到pick_code' % torrent_name)
                        continue
                    #此时有bom.....................
                    #ret = ret[3:]
                    #妈蛋你们搞来搞去是闹哪样
                    ret = json.loads(ret)
                    pick_code = ret['pick_code'].encode('utf-8')
                else:
                    #115一定是默默地star了我...
                    get_url = 'http://web.api.115.com/files/search?offset=0&limit=30&search_value=%s' \
                    '&date=&aid=-1&pick_code=&type=&source=&format=json' % (torrent_name)
                    resp, ret = self.http.get(get_url)
                    if not resp['status'] == 200:
                        logging.error(('%s 创建礼包失败:请求失败' % torrent_name).decode('utf-8'))
                        continue
                    ret = json.loads(ret)
                    if ret['count'] == 0:
                        logging.info(('%s 创建礼包失败,未找到下载的文件,请稍后再试' % torrent_name).decode('utf-8'))
                        continue
                    pick_code = ret['data'][0]['pc']
                #创建礼包
                post_url = BASE_URL + '/?ct=filegift&ac=create'
                post_data = {'pickcodes[]': pick_code}
                resp, ret = self.http.post(post_url, post_data)
                if not resp['status'] == 200:
                    logging.error(('%s 创建礼包失败:请求失败' % torrent_name).decode('utf-8'))
                    continue
                ret = json.loads(ret)
                if ret['state'] is False:
                    logging.error(('%s 创建礼包失败:%s' % (torrent_name, ret['message'].encode('utf-8'))).decode('utf-8'))
                    continue
                gift_code = ret['gift_code'].encode('utf-8')
                #保存礼包名字
                post_url = BASE_URL + '/?ct=filegift&ac=update_remark'
                post_data = {'gift_code': gift_code,
                             'remark': torrent_name}
                resp, ret = self.http.post(post_url, post_data)
                if not resp['status'] == 200:
                    logging.error(('%s 创建礼包失败:请求失败' % torrent_name).decode('utf-8'))
                    continue
                ret = json.loads(ret)
                result.append({'Code': gift_code, 'Name': torrent_name})
                logging.info(('生成礼包成功:Code=%s Hash=%s Name=%s' %
                             (gift_code, self.torrents[i]['info_hash'].encode('utf-8'), torrent_name)).decode('utf-8'))
                #115从完成列表中删除
                if delfromlist is True:
                    post_url = BASE_URL + '/lixian/?ct=lixian&ac=task_del'
                    post_data = {'hash[0]': self.torrents[i]['info_hash'].encode('utf-8'),
                                 'uid': self.uid,
                                 'sign': self.sign,
                                 'time': self.time}
                    self.http.post(post_url, post_data)
                    #logging.info('删除完成任务:Code=%s Hash=%s Name=%s' %
                    #             (gift_code.encode('utf-8'),
                    #              self.torrents[i]['info_hash'].encode('utf-8'), torrent_name))
        return True, result

if __name__ == "__main__":
    u115 = u115_api()
    u115.login('13125180000', '000000')
    #print u115.ret_current_bt_task_count()
    #u115.print_bt_task_info()
    #u115.add_http_task('http://down.360safe.com/360/inst.exe')
    #u115.add_torrent_task('2.torrent')
    #ret, result = u115.auto_make_share_link()
    #print result