
from urlparse import urlparse
import urllib2
import sys
import os
import hashlib

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        # print filenames
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    print 'current_size:',
    print total_size
    return total_size

cache_dir = 'cache'

def initialize_cache():
    size = get_size(cache_dir)

    while size < 10000000:
        try:
            request = 'http://52.4.98.110:8080/wiki/Special:Random'
            response = urllib2.urlopen(request)
            parse_url = urlparse(response.geturl())
            path = parse_url.path
            print 'path', path
        except urllib2.URLError as ue:
            print 'ue',ue
            print 'Sub process ended'
            break
        else:
            namehash = str(int(hashlib.sha1(path).hexdigest(), 16))
            filename = os.getcwd() + '/cache/' + namehash
            try:
                # Handle write exception
                f = open(filename, 'w')
                f.write(response.read())
            except IOError as ue:
                print 'Can not write, Wiki folder exceed memory size limit'
                break
        size = get_size(cache_dir)


initialize_cache()