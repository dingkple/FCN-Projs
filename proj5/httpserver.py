#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import httplib
import urllib
import errno
import commands
import os
import sys
import time
import hashlib
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn
import functools
from itertools import ifilterfalse
from heapq import nsmallest
from operator import itemgetter
import gzip



DEBUG = True


class Counter(dict):
    'Mapping where default values are zero'
    def __missing__(self, key):
        return 0

# reference: http://en.sharejs.com/python/13402

def lfu_cache(maxsize=100):
    '''Least-frequenty-used cache decorator.

    Arguments to the cached function must be hashable.
    Cache performance statistics stored in f.hits and f.misses.
    Clear the cache with f.clear().
    http://en.wikipedia.org/wiki/Least_Frequently_Used

    '''
    def decorating_function(user_function):
        # times each key has been accessed
        use_count = Counter()
        def initial():
            res = []
            dirpath = os.getcwd() + '/cache/'
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            for f in os.listdir(dirpath):
                fpath = dirpath + '/' + f
                fp = gzip.open(fpath)
                fdata = fp.read()
                res.append(f)
                use_count[f] = 1
            return res
        # cache the earlier query
        cache = initial()                               
        cache_dir = 'cache/'

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            print use_count
            key = args[-2:]
            if kwds:
                key += (kwd_mark,) + tuple(sorted(kwds.items()))
            strkey = ''.join(key)
            namehash = str(int(hashlib.sha1(strkey).hexdigest(), 16))
            filename = os.getcwd() + '/cache/' + namehash
            result = ''
            if namehash in cache:
                try:
                    use_count[namehash] += 1
                    fp = gzip.open(filename, 'r')
                    result = fp.read()
                    fp.close()
                    wrapper.hits += 1
                    return (200, result)
                except:
                    pass
            result = user_function(*args, **kwds)
            code = result[0]
            data = result[1]
            url = result[2]
            if url.startswith('http://'):
                url = url[7:]
            else:
                if DEBUG:
                    print url
            is_cached = False
            trial_num = 0
            while not is_cached and trial_num < 4:
                trial_num += 1
                try:
                    if code == 200:
                        if url != strkey:
                            namehash = str(int(hashlib.sha1(url).hexdigest(), 16))
                            use_count[namehash] = 1
                            filename = os.getcwd() + '/cache/' + namehash
                        f = gzip.open(filename, 'w')
                        f.write(data)
                        is_cached = True
                        cache.append(namehash)
                except IOError as e:
                    # disk quota exceeded
                    dirpath = os.getcwd() + '/cache/'
                    if not os.path.exists(dirpath):
                        os.makedirs(dirpath)
                    if e.errno == errno.EDQUOT:
                        print 'quota exceeded'
                        for key, _ in nsmallest(maxsize,
                                        use_count.iteritems(),
                                        key=itemgetter(1)):
                            cache.remove(namehash)
                            del use_count[namehash]
                            os.remove(filename)
                            print ' %s is removed' % removed
                    else:
                        pass
            f.close()
            wrapper.misses += 1
            return (code, data)

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper
    return decorating_function

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    '''Thread for HTTPServer'''.
    pass

class MyHTTPHandler(BaseHTTPRequestHandler):
    '''HTTP handler'''.
    def __init__(self, origin, *args):
        self.origin = origin
        BaseHTTPRequestHandler.__init__(self, *args)

    @lfu_cache(maxsize=200)
    def fetch_content_from_origin(self, host, path):
        '''fetch content from the original server, the function
        is added by a decorator: lfu_cache, it's called when 
        (host, path) pair is not in the cache '''.
        namehash = str(int(hashlib.sha1(path).hexdigest(), 16))
        status = 0
        location = ''
        data = ''
        try:
            url = 'http://' + host + path 
            response = urllib.urlopen(url)
            data = response.read()
            code = response.getcode()
            new_url = response.geturl()
            return code, data, new_url
        except StandardError as e:
            print 'error: '
            print e
            return (404, '', url)

    def do_GET(self):
        ''' the GET function, try to read from cache first, if 
        no cache exists, fetch from the original '''.
        if DEBUG:
            print 'doing getting'
        host = self.origin + ':8080'
        if DEBUG:
            print host
            print self.path
        result = self.fetch_content_from_origin(host, self.path)
        # if result is not None:
        self.send_response(result[0])
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(result[1])
                
    # def cache_file_to_disk(self, a_file, data):
    #     if DEBUG:
    #         print 'caching: '
    #     filename = os.getcwd() + '/cache/' + a_file
    #     d = os.path.dirname(filename)
    #     is_cached = False

    #     if not os.path.exists(d):
    #         os.makedirs(d)
    #     f = gzip.open(filename, 'w')
    #     while not is_cached:
    #         try:
    #             f.write(data)
    #             is_cached = True
    #         except IOError as e:
    #             # disk quota exceeded
    #             if e.errno == errno.EDQUOT:
    #                 print 'quota exceeded'
    #                 os.remove(os.curdir + '/cache/' + filename)
    #                 print ' %s is removed' % removed
    #             else:
    #                 pass
    #     f.close()


def main(port, origin):
    def myHandler(*args):
        MyHTTPHandler(origin, *args)

    server = ThreadedHTTPServer(('', port), myHandler)

    server.allow_reuse_address = True
    if DEBUG:
        print time.asctime(), "Server Starts @Port %s" % (port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    # os.system("rm -rf cache")
    if DEBUG:
        print time.asctime(), "Server Stops @Port %s" % (port)


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) != 5 or argv[1] != '-p' or argv[3] != '-o':
        sys.exit("command format error: ./httpserver -p <port> -o <origin>")
    port = int(argv[2])
    origin = argv[4]
    main(port, origin)