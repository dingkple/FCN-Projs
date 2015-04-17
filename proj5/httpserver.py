#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import sys
import time
import hashlib
import httplib
import errno
import commands
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn
import functools
from itertools import ifilterfalse
from heapq import nsmallest
from operator import itemgetter



DEBUG = True

CACHE_INDEX = []


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
        cache = {}                      # mapping of args to results
        use_count = Counter()           # times each key has been accessed
        kwd_mark = object()             # separate positional and keyword args

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            key = args[-2:]
            if kwds:
                key += (kwd_mark,) + tuple(sorted(kwds.items()))
            use_count[key] += 1

            # get cache entry or compute if not found
            try:
                result = cache[key]
                wrapper.hits += 1
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                wrapper.misses += 1

                # purge least frequently used cache entry
                if len(cache) > maxsize:
                    for key, _ in nsmallest(maxsize // 10,
                                            use_count.iteritems(),
                                            key=itemgetter(1)):
                        del cache[key], use_count[key]

            return result

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper
    return decorating_function

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class MyHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, origin, *args):
        self.origin = origin
        BaseHTTPRequestHandler.__init__(self, *args)

    @lfu_cache(maxsize=200)
    def fetch_content_from_origin(self, host, path):
        namehash = str(int(hashlib.sha1(path).hexdigest(), 16))
        status = 0
        location = ''
        data = ''
        try:
            conn = httplib.HTTPConnection(host)
            conn.request("GET", path)
            response = conn.getresponse()
            status = response.status
            location = response.getheader('Location')
            data = response.read()
            self.cache_file_to_disk(namehash, data)
            return (status, location, data)
        except StandardError as e:
            print e
            return None

    def do_GET(self):
        global CACHE_INDEX
        if DEBUG:
            print 'doing getting'
        host = self.origin + ':8080'
        if DEBUG:
            print host
            print self.path
        (status, location, data) = self.fetch_content_from_origin(host, self.path)
        if DEBUG:
            print status
            print location
        if status == 301 or status == 302:
            self.send_response(status)
            self.send_header('Content-type', 'text/html')
            o = urlparse(location)
            new_location = 'http://' + self.origin + ':8080' + o.path
            print new_location
            self.send_header('Location', new_location)
            self.end_headers()
            self.wfile.write(data)

        # For 200, 404 status code, the data section contains everything the client need
        # only cache this part 
        else:
            self.send_response(status)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(data)
            
            # save the received from the pipe
                
    def cache_file_to_disk(self, a_file, data):
        if DEBUG:
            print 'caching: '
        filename = os.getcwd() + '/cache/' + a_file
        d = os.path.dirname(filename)
        is_cached = False

        if not os.path.exists(d):
            os.makedirs(d)

        f = open(filename, 'w')
        while not is_cached:
            try:
                f.write(data)
                is_cached = True
            except IOError as e:
                # disk quota exceeded
                if e.errno == errno.EDQUOT:
                    print 'quota exceeded'
                    os.remove(os.curdir + '/cache/' + filename)
                    print ' %s is removed' % removed
                else:
                    pass
        f.close()


def main(port, origin):
    def myHandler(*args):
        MyHTTPHandler(origin, *args)

    server = ThreadedHTTPServer(('', port), myHandler)

    # Prevent issues with socket reuse
    server.allow_reuse_address = True
    if DEBUG:
        print time.asctime(), "Server Starts @Port %s" % (port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    os.system("rm -rf cache")
    if DEBUG:
        print time.asctime(), "Server Stops @Port %s" % (port)


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) != 5 or argv[1] != '-p' or argv[3] != '-o':
        sys.exit("command format error: ./httpserver -p <port> -o <origin>")
    port = int(argv[2])
    origin = argv[4]
    try:
        f = open('ec2-hosts.txt', 'r')
        cdnname = f.read().split()[0]
    except IOError:
        print 'Cannot open ec2-hosts.txt file'
        cdnname = ''
    main(port, origin)