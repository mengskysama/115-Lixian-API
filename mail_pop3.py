#!/usr/bin/env python
# -*- coding: utf-8 -*-

import poplib
import base64
import re

def check_mail_url(mail, passwd):
    #pop3服务器地址
    host = mail.find('@')
    if host == -1:
        print '邮箱格式非法'
        return
    host = 'pop.' +  mail[host + 1:]
    # 创建一个pop3对象，这个时候实际上已经连接上服务器了
    pp = poplib.POP3(host)
    # 设置调试模式，可以看到与服务器的交互信息
    pp.set_debuglevel(1)
    # 向服务器发送用户名
    pp.user(mail)
    # 向服务器发送密码
    pp.pass_(passwd)
    # 获取服务器上信件信息，返回是一个列表，第一项是一共有多上封邮件，第二项是共有多少字节
    ret = pp.stat()

    last_letter = ret[0]
    if last_letter == 0:
        print '似乎没有收到邮件'
        pp.quit()
        return

    down = pp.retr(last_letter)
    if down[1][0].find('mail.115.com') == -1:
        print '似乎没有收到115的邮件'
        pp.quit()
        return

    print '115邮件GET'

    #求不吐槽
    context = ''
    begin = 0
    for line in down[1]:
        if line == '' and context == '':
            begin = 1
            continue
        if line == '':
            break
        if begin == 1:
            context += line

    main = base64.decodestring(context)
    reg = re.compile('<a href="(\S+)"')
    hrefs = re.findall(reg, main)
    if len(hrefs) < 2:
        print '获取激活链接失败:似乎没有找到?'
        pp.quit()
        return

    return str(hrefs[1])
    pp.quit()

if __name__ == "__main__":
    print check_mail_url('hdtts@126.com', '123456')