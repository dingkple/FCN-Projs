
import time
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import hashlib
import httplib
import errno
import commands
import os
import sys
import time
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn
import functools
from itertools import ifilterfalse
from heapq import nsmallest
from operator import itemgetter

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
        cache_dir = 'cache'

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

        def initial():
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fpath = dirpath + '/' + f
                    with open(fpath) as f:
                        fdata = f.read()
                        cache[f] = fdata
                        use_count[f] = 1

        def clear():
            cache.clear()
            use_count.clear()
            wrapper.hits = wrapper.misses = 0

        wrapper.hits = wrapper.misses = 0
        wrapper.clear = clear
        return wrapper
    return decorating_function







@lfu_cache(maxsize=200)
def fetch_content_from_origin(host, path):
    print host,
    print path
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
        a_file = [host, path]
        self.cache_file_to_disk(a_file, data)
        return (status, location, data)
    except StandardError as e:
        print e
        return None



host = 'http://ec2-52-4-98-110.compute-1.amazonaws.com:8080'
path = '/wiki/Portal:Current_events'


for i in range(5):
    res = fetch_content_from_origin(host, path)
    print res
    print res[0]



















