#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

class http_request:

    def __init__(self, cookie=None):
        self.set_cookie = None
        self.cookies = requests.cookies.RequestsCookieJar()

    def post(self, url, body=None):
        try:
            r = requests.post(url=url, data=body, cookies=self.cookies, timeout=10.0)
            resp = {'status': r.status_code}
            content = r.text
            for c in r.cookies:
                self.cookies.set_cookie(c)
        except Exception, e:
            resp = {'status': 600}
            content = 'HttpHelper: %s' % e
        return resp, content

    def upload(self, url, files):
        try:
            headers = {'User-Agent': 'Shockwave Flash'}
            r = requests.post(url=url, files=files, cookies=self.cookies, headers=headers, timeout=60.0)
            resp = {'status': r.status_code}
            content = r.text
            for c in r.cookies:
                self.cookies.set_cookie(c)
        except Exception, e:
            resp = {'status': 600}
            content = 'HttpHelper: %s' % e
        return resp, content

    def get(self, url, _headers=None):
        try:
            r = requests.get(url=url, cookies=self.cookies, timeout=10.0)
            resp = {'status': r.status_code}
            content = r.text
            for c in r.cookies:
                self.cookies.set_cookie(c)
        except Exception, e:
            resp = {'status': 600}
            content = 'HttpHelper: %s' % e
        return resp, content

if __name__ == "__main__":
    http = http_request()
    resp, ret = http.get("http://www.baidu.com")
    print ret
