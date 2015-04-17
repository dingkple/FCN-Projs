#! /usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os, sys, time, hashlib, httplib, errno, commands
from urlparse import urlparse, parse_qs
from SocketServer import ThreadingMixIn

DEBUG = True

CACHE_INDEX = []

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class MyHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, origin, *args):
        self.origin = origin
        BaseHTTPRequestHandler.__init__(self, *args)

    def fetch_from_original(self, host, path):
        ''' Retrieves the content from the origin server
            Returns the status code, redirection information, and the data 
        '''
        try:
            conn = httplib.HTTPConnection(host)
            conn.request("GET", path)
            response = conn.getresponse()
            status = response.status
            location = response.getheader('Location')
            data = response.read()
            return (status, location, data)
        except StandardError:
            return None

    def do_GET(self):
        ''' Response to clients' GET requests, fulfill from local cache or retrieve from origin and deliver
        '''
        global CACHE_INDEX
        if DEBUG:
            print 'doing getting'
        # create hashdigest for every requested file
        name_hash = int(hashlib.sha1(self.path).hexdigest(), 16)
        cache_file = str(name_hash)
        if cache_file in CACHE_INDEX:
            with open(os.curdir + '/cache/' + cache_file) as page:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(page.read())

            # refresh the order of the cache
            CACHE_INDEX.remove(cache_file)
            CACHE_INDEX.insert(0, cache_file)

        elif cache_file not in CACHE_INDEX:
            host = self.origin + ':8080'
            if DEBUG:
                print host
                print self.path
            (status, location, data) = self.fetch_from_original(host, self.path)
            if DEBUG:
                print status
                print location
                print data

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
                self.cache_file_to_disk(cache_file, data)
                
    def cache_file_to_disk(self, a_file, data):
        ''' Save the given data to local disk, if disk full eliminate the oldest fetched item
        '''
        global CACHE_INDEX

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
                CACHE_INDEX.append(a_file)
            except IOError as e:
                # disk quota exceeded
                if e.errno == errno.EDQUOT:
                    print 'quota exceeded'
                    removed = CACHE_INDEX.pop()
                    os.remove(os.curdir + '/cache/' + removed)
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