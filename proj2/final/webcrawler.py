#!/usr/bin/python
import socket
import urlparse
import os
import re
import time
import sys
import htmlentitydefs
import threading

#This file contains the class for shared infomation
from SharingInfo import *


#simple http 
from MultiThreadUrllib import Myurllib


"""

This is multi-thread version of crawler, setting 50 threads takes about 2-4 minutes to get

all the 5 flags. 

Note this crawler only runs on 'http://cs5700sp15.ccs.neu.edu/', for more general purples,

it still needs pretty much work

"""


class mycrawler(threading.Thread):

    # a thread, lock is the shared lock, sharing stores the common-info, for detials see SharingInfo
    def __init__(self, name, lock = None, sharing = None, cookies = {}, uname = '001710157', pwd = 'Y83VV8X1', print_flags = False):
    	threading.Thread.__init__(self)
        self.username = uname
        self.password = pwd
        self.login_url = 'http://cs5700sp15.ccs.neu.edu/accounts/login/'
        self.data_url = 'http://cs5700sp15.ccs.neu.edu/'
        self.mylib = Myurllib(cookies)
        self.visited_file = 'visited_urls.txt'
        self.file = None
        self.pages = ''
        self.counter = 0
        self.error_file = 'error_url.txt'
        self.is_login = False
        self.pirnt_processing_url = print_flags
        self.temp_pages = []
        self.name = name
        self.lock = lock
        self.sharing = sharing

    # @page is the data from the server
    # @return all the url in the cs5700sp15.ccs.neu.edu
    # since we should just crawl the required host, all the urls should starts with '/'
    def detect_url(self, page):
        new_urls = []
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', page)
        for url in urls:
            if url not in self.sharing.visited_urls and url not in self.sharing.url_stack:
                if url[:1] == '/':
                    if self.pirnt_processing_url:
                        print url
                    new_urls.append(url)
        return new_urls

    #generate the real url and try to get the page from the server
    def try_get(self, url):
        if self.pirnt_processing_url:
             print "try_getting " + url
        if url[:1] == '/':
        	url = self.data_url + url[1:]
        page = self.mylib.GET(url)
        if len(page) > 0 and self.get_statues_code(page) > 0:
            self.mylib.update_cookies(page)
        return page

    #login process mainly takes 3 steps: 
    # 1. send a get to the server to fetch the login html
    #   since the login html contains 2 cookies, put them in a dict and store them
    # 2. send a post using the cookies, then the server will give a new sessionid,
    #   with a 302 found header, that mean you've already loged in
    # 3. replace the old sessionid with the new one, and send  a get using all the
    #   two cookies, now it's time for crawling
    def login(self):
        # paras = {"username":"001710157", "password":"Y83VV8X1", "next":"\/fakebook\/"}
        paras = {}
        paras['username'] = self.username
        paras['password'] = self.password
        paras['next'] = '\/fakebook\/'

        page = self.try_get(self.login_url)
        csrftoken = re.findall(r"name='csrfmiddlewaretoken' value='*([^'']+)", page)
        if len(csrftoken) > 0:
            paras["csrfmiddlewaretoken"] = csrftoken[0]
        else:
            return
        page = self.mylib.POST(self.login_url, paras)
        self.mylib.update_cookies(page)
        if self.get_statues_code(page) == '302':
            page = self.try_get('/fakebook/')
            if self.get_statues_code(page) == '200':
                self.is_login = True
        else:
            if self.pirnt_processing_url:
                print 'login in with status code: ' + str(self.get_statues_code(page))

    #simple, use regular expression to find flags
    def search_secret_flag(self, page, url):
        flags = re.findall(r"FLAG: *([^<]+)", page)
        if len(flags) > 0:
            self.lock.acquire()
            try:
                self.sharing.secret_flag[flags[0]] = url
                self.sharing.flag_counter += 1
                print flags[0]
            finally:
                self.lock.release()
            

    #main method for crawling: 
    # 1. first, fill the stack using the '/fakebook/', all the threads starts here
    # 2. the try to pop the first url, since all the threads starts from the same stack,
    #     it's possible that sometimes there's no url in the stack, so the thread needs to 
    #     wait for a short time for other threads find new url and push them
    # 3. when a url is poped out, send a get to get the page count, then parse it, detect 
    #     new urls in this page, push them, and find if it contains the secret_flag, if yes
    #     apply a lock for the shaing class, store the flag, change the counter. if not, 
    #     just process the page according to the status of the page, if 200, it's all set.
    #     prepare for the next one. if 302, find the relocation url, if 403 or 404, do nothing
    #     if 500, push it again, regardless of the visited_pool
    # 4. if there's already 5 flags, just return.
    # 5. if less than 5 and the stack is empty, probably the server is down...I haven't encountered
    #    this problem under normal cirmustances
    def crawl_fakebook(self):
        # if not self.is_login:
        #     print 'LOGIN ERROR!!!'
        #     return
        page = None
        stops = 1
        new_url = self.detect_url(self.try_get(self.data_url))
        self.sharing.url_stack.extend(new_url)
        self.sharing.visited_urls.extend(new_url)
        try:
            self.lock.acquire()
            while len(self.sharing.url_stack) == 0:
                self.lock.release()
                time.sleep(1)
                self.lock.acquire()
            url = self.sharing.url_stack.pop()
        finally:
            self.lock.release()
        try:
            while self.sharing.flag_counter < 5:
            # while True and not self.sharing.is_flag_written:
                new_url = self.parse_page(self.try_get(url), url)
                self.lock.acquire()
                try:
                    self.sharing.url_stack.extend(new_url)
                    self.sharing.visited_urls.extend(new_url)
                    if len(self.sharing.url_stack) == 0:
                        break
                    num = 0
                    while len(self.sharing.url_stack) == 0:
                        print "traped!!!" + " " + self.name
                        self.lock.release()
                        # in most cases, this situation won't happen
                        if pirnt_processing_url:
                            print 'empty stock now'
                        time.sleep(1)
                        num += 1
                        if num > 10:
                            break
                        self.lock.acquire()
                    if num > 10:
                        # self.lock.release()
                        break
                    url = self.sharing.url_stack.pop()
                    self.sharing.page_counter += 1
                    # if self.pirnt_processing_url:
                    # print str(self.sharing.page_counter) + " " + str(self.sharing.flag_counter)
                finally:
                	self.lock.release()
        finally:
            # print 'thread: ' + self.name + "'s fight is over!"     
            # if self.sharing.secret_flag is not None and len(self.sharing.secret_flag) > 4:
            #     self.write_secret_flag()
            #     pass
            # else:
            #     pass
            #     print len(self.sharing.url_stack)
            #     print 'CAN NOT FIND FLAGS',
            #     print 'FOUND : ' + str(len(self.sharing.secret_flag))
            #     if len(self.sharing.secret_flag) > 0:
            #         self.write_secret_flag()
            pass

    # nothing much about this method, almost covered by last method
    def parse_page(self, page, url):
        status = self.get_statues_code(page)
        new_urls = []
        if status == '200':
            self.counter += 1
            if url[:1] != '/':
                self.pages += url[29:] + "    " + status + "\r\n"
            else:
                self.pages += url + "    " + status + "\r\n"
            if self.pirnt_processing_url:
                print self.pages + "self.pages"
            self.search_secret_flag(page, url)
            # self.mylib.update_cookies(page)
            new_urls = (self.detect_url(page))
            # if self.counter % 30 == 0 and self.pages is not None:
            #     self.write_down_disk()
        elif status == '302' or status == '301':
            new_urls = self.detect_url(url)
            if len(new_urls) == 0:
                new_urls.append(url)
        elif status == '403' or status == '404':
            pass
        elif status == '500':
            new_urls.append(url)
        return new_urls

    # print all flags:
    def print_flags(self):
        for flag in self.sharing.secret_flag.keys():
            print flag

    # get the status cocd from the page
    def get_statues_code(self, page):
        status = re.findall(r'HTTP/1.1 (.*?) ', page)
        if len(status) > 0:
            return status[0]
        else:
            return '-1'

    #start the thread
    def run(self):
        num = 0
        self.crawl_fakebook()


#start multi-thread crawler, default set number of threads: 50
def run_multi_thread(username='001710157', password='Y83VV8X1'):
    sharing = sharingInfo()
    mylock = threading.Lock()
    threads = []
    loginCrawler = mycrawler('login', uname = username, pwd = password)
    num = 0
    while not loginCrawler.is_login:
        loginCrawler.login()
        time.sleep(1)
        # print 'loging: ' + str(num)
        num += 1
    # print loginCrawler.mylib.cookies
    for i in range(150):
        t = mycrawler('crawler'+str(i), lock = mylock, sharing = sharing, cookies = loginCrawler.mylib.cookies, uname = username, pwd = password)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


def main():
    m = None
    if len(sys.argv) > 1:
        if len(sys.argv) == 3:
            run_multi_thread(sys.argv[1], sys.argv[2])
        else:
            print 'check your parameters!'
            exit(0)
    else:
        run_multi_thread()


if __name__ == '__main__':
    main()



