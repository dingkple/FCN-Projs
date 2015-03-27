#!/usr/bin/python
import socket
import urlparse
import os
import re
import time
import htmlentitydefs
import threading


class Myurllib():

    def __init__(self, cookies):
        self.cookies = cookies

    def set_cookies(self, name, value):
        self.cookies[name] = value

    def recv_timeout(self, sock):
        f = sock.makefile('rb')
        datas = []
        d = f.readline()
        while f and d:
            datas.append(d)
            d = f.readline()
                
        return ''.join(datas)

    #update cookies, it's better if store cookies separately for different websites, but since there's only one 
    #here, doesn't matter much
    def update_cookies(self, page):
        new_cookies = re.findall(r'Set-Cookie: *([^;]+)', page)
        names = []
        values = []
        for i in range(len(new_cookies)):
            names.append(new_cookies[i][0:9])
            values.append(new_cookies[i][10:len(new_cookies[i])])
            self.cookies[names[i]] = values[i]

    #generate the cookies line for a header in a post or get
    def header_of_cookies(self):
        cookies = "Cookie: "
        n = 0
        num_cookies = len(self.cookies.keys())
        for key in self.cookies.keys():
            n+=1
            cookies += key + "="
            cookies += self.cookies[key]
            if n < num_cookies:
                cookies += "; "
        return cookies+"\r\n"

    #Some lines in this method also refered to code from the Intenet, I generated the header by
    #checking the request header in Chrome, saved a lot of time.
    def GET(self, url):
        data = ''
        url = urlparse.urlparse(url)
        # print url
        path = url.path
        if path == "":
            path = "/"
        HOST = url.netloc  # The remote host
        PORT = 80          # The same port as used by the server
        # create an INET, STREAMing socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect((HOST, PORT))
            header = 'GET %s HTTP/1.0\r\n' % (url.path)
            header += 'Connection: keep-alive\r\n'
            header += 'Cache-Control: max-age=0\r\n'
            header += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
            header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
            if len(self.cookies) > 0:
                header += self.header_of_cookies()
            header += "\r\n"
            s.send(header)

            data = self.recv_timeout(s)
            s.shutdown(1)
            s.close()
        finally:
            return data

    #get the parameter part for the header    
    def get_paras_header(self, parameters = None):
        if parameters is None:
            return None
        paras = '\r\nusername=%s&password=%s&csrfmiddlewaretoken=%s&next=' % (parameters['username'], parameters['password'], parameters['csrfmiddlewaretoken'])
        return paras + "\r\n\r\n"

    #do post
    def POST(self, url, parameters = None):
        url = urlparse.urlparse(url)
        path = url.path
        if path == "":
            path = "/"
        HOST = url.netloc  
        PORT = 80        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.connect((HOST, PORT))
            header = 'POST %s HTTP/1.0\r\n' % (url.path)
            header += 'Connection: keep-alive\r\n'
            header += 'Content-Length: 95\r\n'
            header += 'Cache-Control: max-age=0\r\n'
            header += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
            header += 'Origin: http://cs5700sp15.ccs.neu.edu\r\n'
            header += 'User-Agent: HTTPTool/1.0\r\n'
            header += 'Content-Type: application/x-www-form-urlencoded\r\n'
            header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
            if len(self.cookies.keys()) > 0:
                header += self.header_of_cookies()
            if parameters is not None:
                header += self.get_paras_header(parameters)
            s.send(header)
            data = self.recv_timeout(s)
        finally:
            s.shutdown(1)
            s.close()
            return data






