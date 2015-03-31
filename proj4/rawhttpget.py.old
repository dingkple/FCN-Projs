#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""


import sys
import raw_tcp
import urlparse
import socket

DEBUG = False
# DEBUG = True


class raw_http:
    """httpget implementation using raw socket"""
    def __init__(self):
        self.tcp = raw_tcp.raw_TCP()
        self.filename = 'index.html'
        self.result = None


    # since we're requested to ensure the file downloaded exactly the same with the ones on server,
    # so if the file is chunked encoded, we need to decode
    def _decode_chucked_data(self):
        pos = 0
        chunked = ''
        now = 0
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
        header += 'User-Agent: Wget/1.13.4(linux-gnu)\r\n'
        # header += 'Cache-Control: max-age=0\r\n'
        # header += 'Accept: text/html,application/xhtmlxml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
        # header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
        header += "\r\n"
        return header

    # find out the filename and send http requests
    def httpget(self, url):
        purl = urlparse.urlparse(url)
        if '/' in purl.path:
            path = purl.path.split('/')
            if path[-1] != '':
                self.filename = path[-1]
        request = self._get_http_header(purl)
        print purl.hostname
        isChunked = self.tcp.send(purl, request)
        self._read_temp()
        if isChunked:
            self._decode_chucked_data()
        self._write_file()

    def _read_temp(self):
        f = open('temp.temp', 'r')
        self.result = ''.join(f.readlines())

    # write the data to file
    def _write_file(self):
        if DEBUG:
            print self.result
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













        