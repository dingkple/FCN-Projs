#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""


import sys
import raw_tcp_FSM
import urlparse
import socket
import re
import os

DEBUG = False
# DEBUG = True


class raw_http:
    """httpget implementation using raw socket"""
    def __init__(self):
        self.tcp = raw_tcp_FSM.raw_TCP()
        self.filename = 'index.html'
        self.result = []
        self.header = ''
        self.isHeaderFound = False
        self.content_length = -1
        self.recv_len = 0
        self.chunked = False
        self.fileWriter = None


    # since we're requested to ensure the file downloaded exactly the same with the ones on server,
    # so if the file is chunked encoded, we need to decode
    def _decode_chucked_data(self):
        pos = 0
        chunked = ''
        now = 0
        self.result = ''.join(self.result)
        while pos < len(self.result):
            pos = self.result.find('\r\n', now)
            try:
                chunked += self.result[pos+2 : pos + 2 + int(self.result[now:pos], 16)]
                now = pos + int(self.result[now:pos], 16) + 4
            except ValueError:
                break
        self.result = chunked


    # get the http request header
    def _get_http_header(self, url):
        path = url.path
        if path == "":
            path = "/"
        header = 'GET %s HTTP/1.1\r\n' % (path)
        header += 'Host: %s\r\n' % (url.hostname)
        header += 'Connection: keep-alive\r\n'
        # header += 'User-Agent: Wget/1.13.4(linux-gnu)\r\n'
        # header += 'Cache-Control: max-age=0\r\n'
        # header += 'Accept: text/html,application/xhtmlxml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
        # header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
        header += "\r\n"
        return header


    def check_header(self):
        if '\r\n\r\n' in self.header:
            res = self.header.split('\r\n\r\n')
            self.header = res[0]
            self.result.append(res[1])
            self.recv_len = self.recv_len - len(self.header) - 4
            if '200' not in self.header:
                print 'http status err'
                sys.exit()
            if 'Content-Length' in self.header:
                cl = re.search(r'[.*?|\s]*Content-Length: ([\d]*)[\s\s].*?', self.header)
                self.content_length = int(cl.groups(1)[0])
            elif 'Transfer-Encoding' in self.header:
                self.chunked = True
            self.isHeaderFound = True


    # find out the filename and send http requests
    def httpget(self, url):
        purl = urlparse.urlparse(url)
        if '/' in purl.path:
            path = purl.path.split('/')
            if path[-1] != '':
                self.filename = path[-1]
        request = self._get_http_header(purl)
        self.tcp.send(purl, request)
        while not self.isHeaderFound:
            recv_len, data = self.tcp.recv()
            self.header += data
            self.recv_len = recv_len
            self.check_header()
        while not self.tcp.is_closed():
            recv_len, data = self.tcp.recv()
            self.recv_len = recv_len - len(self.header) - 5 + len(data)
            if self.content_length != -1:
                size_str = '%06.02f KB / %d KB downloaded!' % (self.recv_len*1.0/1024, self.content_length)
            else:
                size_str = '%02f KB / ---- KB downloaded!' % (self.recv_len*1.0/1024)
            # print size_str
            sys.stdout.write('%s\r' % size_str)
            sys.stdout.flush()  

            if self.content_length != -1:
                self._write_to_file(data)
                if self.content_length == self.recv_len: 
                    self._close_file()
                    if not self.tcp.is_closed(): 
                        self.tcp.init_tear_down()
                    break
            elif self.chunked:
                self.result.append(data)
                if data.endswith('0\r\n\r\n'):
                    self._write_file()
                    if not self.tcp.is_closed():
                        self.tcp.init_tear_down()
                    break

    def _write_to_file(self, data):
        if self.fileWriter == None:
            self.fileWriter = open(self.filename, 'w')
        self.fileWriter.write(data)

    def _close_file(self):
        self.fileWriter.close()

    # write the data to file
    def _write_file(self):
        if DEBUG:
            print self.result
        self._decode_chucked_data()
        if '.' in self.filename and self.filename.split('.')[1] in ['html', 'htm']:
            f = open(self.filename, 'w')
            f.write(self.result)
            f.close()
        else:
            f = open(self.filename, 'wb')
            f.write(self.result)
            f.close()



def main():
    http = raw_http()
    if len(sys.argv) != 2:
        print 'argv error'
    else:
        http.httpget(sys.argv[1])

if __name__ == '__main__':
    main()













        