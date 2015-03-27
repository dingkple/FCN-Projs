import socket
import urlparse
import os
import re
import time
import sys
import htmlentitydefs

from Myurllib import Myurllib

socket.setdefaulttimeout = 0.50
os.environ['no_proxy'] = '127.0.0.1,localhost'
linkRegex = re.compile('<a\s*href=[\'|"](.*?)[\'"].*?>')
testRegex = re.compile('href')
CRLF = "\r\n\r\n"


"""
NOTE :

This is the first version of the crawler, single-thread, takes about 1h to 
get all the 5 flags





"""

class mycrawler:

    def __init__(self, uname = '001710157', pwd = 'Y83VV8X1'):
        self.username = uname
        self.password = pwd
        self.secret_mark = "<h2 class='secret_flag' style='color:red'>"
        self.login_url = 'http://cs5700sp15.ccs.neu.edu/accounts/login/'
        self.data_url = 'http://cs5700sp15.ccs.neu.edu/'
        self.mylib = Myurllib()
        self.visited = []
        self.stack = []
        self.secret_flag = {}
        self.start_url = ''
        self.visited_file = 'visited_urls.txt'
        self.file = self.get_file()
        self.pages = ''
        self.counter = 0
        self.error_file = 'error_url.txt'
        self.flag_counter = 0
        self.is_login = False
        self.pirnt_processing_url = False
        # self.connection = self.login()


    def get_file(self):
        path = os.getcwd()
        path = path + '/' + self.visited_file
        # print path
        self.file = open(path, 'a+')

    def handle_302_page(self, page):
        new_url = re.findall(r'Location: *([^\r\n]+)', page)
        self.mylib.update_cookies(page)
        # print len(new_url),
        # print " new_url"
        # print new_url
        page = self.mylib.GET(new_url[0])
        self.mylib.update_cookies(page)
        return page


    def detect_url(self, page):
        # print "detecting url"
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', page)
        for url in urls:
            if url not in self.visited:
                if url[:1] == '/':
                    if len(self.stack) == 0:
                        self.start_url = url
                    if self.pirnt_processing_url:
                        print url
                    self.visited.append(url)
                    self.stack.append(url)

    def try_get(self, url):
        if self.pirnt_processing_url:
             print "try_getting " + url
        page = self.mylib.GET(url)
        if len(page) > 0 and self.mylib.get_statues_code(page) > 0:
            self.mylib.update_cookies(page)
        return page

    def login(self):
        paras = {"username":"001710157", "password":"Y83VV8X1", "next":"\/fakebook\/"}

        page = self.try_get(self.login_url)
        # if self.mylib.get_statues_code(page) == '302':
        #     page = self.handle_302_page(page)
        # elif self.mylib.get_statues_code(page) == '200':
        #     self.mylib.update_cookies(page)
        # print len(page)
        # print page
        # res = parser.feed(page)
        # print res
        csrftoken = re.findall(r"name='csrfmiddlewaretoken' value='*([^'']+)", page)
        paras["csrfmiddlewaretoken"] = csrftoken[0]
        page = self.mylib.POST(self.login_url, paras)
        self.mylib.update_cookies(page)
        # print csrftoken 
        # print page
        # if self..mylib.get_statues_code(page) == '302':
        #     self.handle_302_page(page)
        # elif self..mylib.get_statues_code(page) == '200':
        #     self.detect_url(page)
        #     return 1
        # else:
        #     return -1
        # print page
        if self.mylib.get_statues_code(page) == '302':
            self.is_login = True
        else:
            # print page
            print 'login in with status code: ' + self.mylib.get_statues_code(page)

    def search_secret_flag(self, page, url):
        flags = re.findall(r"FLAG: *([^<]+)", page)
        if len(flags) > 0:
            self.secret_flag[flags[0]] = url
            self.flag_counter += 1
            print flags[0]
            return True
        else:
            return False

    def fill_start_url(self):
        self.detect_url(self.try_get(self.data_url + "fakebook/"))


    def crawl_fakebook(self):
        if not self.is_login:
            print 'LOGIN ERROR!!!'
            return
        page = None
        self.detect_url(self.try_get(self.data_url))
        try:
            while self.flag_counter < 5 and len(self.stack) > 0:
                if len(self.stack) == 0:
                    break;

                url = self.stack.pop()

                if len(url) > 0 and url[0] == '/':
                    url = self.data_url + url[1:]
                    page = self.try_get(url)
                    self.parse_page(page, url)
        finally:
            if self.secret_flag is not None and len(self.secret_flag) > 4:
                self.write_secret_flag()
                # self.print_flags()
                # print self.secret_flag
            else:
                print 'CAN NOT FIND FLAGS',
                print 'FOUND : ' + str(len(self.secret_flag))
                if len(self.secret_flag) > 0:
                    self.write_secret_flag()

    def print_flags(self):
        for flag in self.secret_flag.keys():
            print flag

    def write_secret_flag(self):
        path = os.getcwd()
        path = path + '/' + 'secret_flag.txt'
        f = open(path, 'a+')
        for flag in self.secret_flag.keys():
             f.write(flag + '\r\n' + self.secret_flag[flag] + '\r\n')
        f.close()


    def write_error_url(self, url):
        path = os.getcwd()
        path = path + '/' + self.error_file
        f = open(path, 'a+')
        f.write(url + '\r\n')
        f.close()


    def write_down_disk(self):
        if self.file is None:
            self.get_file
        self.file.write(self.pages)
        self.file.close()
        self.file = None
        self.pages = ''

    def parse_page(self, page, url):
        status = self.mylib.get_statues_code(page)
        if self.file is None:
            self.get_file()
        if status == '200':
            self.counter += 1
            # self.file.write(url + "    " + status + "\r\n")
            self.pages += url[29:] + "    " + status + "\r\n"
            self.search_secret_flag(page, url)
            self.detect_url(page)
            if self.counter % 10 == 0:
                self.write_down_disk()
        elif status == '302':
            self.detect_url(url)
        elif status == '403' or status == '404':
            pass
        elif status == '500':
            self.stack.append(url)
        elif len(page) == 0:
            self.write_error_url(url)
            # self.stack.append(url)
            # exit(0)


def main():
    m = None
    if len(sys.argv) > 1:
        if len(sys.argv) == 3:
            m = mycrawler(sys.argv[1], sys.argv[2])
            m.login()
            m.crawl_fakebook()
        else:
            print 'check your parameters, dumb ass!'
            exit(0)
    else:
        m = mycrawler()
        m.login()
        m.crawl_fakebook()






if __name__ == '__main__':
    main()





