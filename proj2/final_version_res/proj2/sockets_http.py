#/usr/bin/python
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
                    print url
                    self.visited.append(url)
                    self.stack.append(url)

    def try_get(self, url):
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
        if len(page) == 0:
            return -1
        else:
            self.detect_url(page)
            return 1

    def search_secret_flag(self, page, url):
        flags = re.findall(r"FLAG: *([^<]+)", page)
        if len(flags) > 0:
            self.secret_flag[flags[0]] = url
            self.flag_counter += 1
            return True
        else:
            return False

    def fill_start_url(self):
        self.detect_url(self.try_get(self.data_url + "fakebook/"))


    def crawl_fakebook(self):
        page = None
        self.detect_url(self.try_get(self.data_url))
        while self.flag_counter < 5 and len(self.stack) > 0:
            if len(self.stack) == 0:
                break;

            url = self.stack.pop()

            if len(url) > 0 and url[0] == '/':
                url = self.data_url + url[1:]
                page = self.try_get(url)
                self.parse_page(page, url)

        if self.secret_flag is not None:
            self.write_secret_flag()
            print self.secret_flag
            return 

    def write_secret_flag(self):
        path = os.getcwd()
        path = path + '/' + 'secret_flag.txt'
        f = open(path, 'a+')
        for flag in self.secret_flag.keys():
             f.write(flag + '\n' + self.secret_flag[flag])
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


    # def read_visited_urls(self):
    #     path = os.getcwd() + '/' + self.visited_file
    #     f = open(path)
    #     for line in f.readlines():
    #         self.visited_file



    def test_secret(self):
        apage = ''
        apage += '<html><head><title>Fakebook</title><style TYPE="text/css"><!--'
        apage += '#pagelist li { display: inline; padding-right: 10px; }'
        apage += "--></style></head><body><h1>Fakebook</h1><p><a href='/fakebook/'>"
        apage += "Home</a></p><hr/><h1><a href='/fakebook/519665189/'>Rimujuvo Plarenn</a></h1><h2>Basic"
        apage += " Information</h2><ul><li>Sex: Female</li><li>Hometown: Waltham</li></ul><h2>Personal"
        apage += " Information</h2><ul></ul><h2>Friends</h2><p><a href='/fakebook/519665189/friends/1/'>"
        apage += " View Rimujuvo Plarenn's friends</a></p><h2>Wall</h2><p>"
        apage += 'Rimujuvo Plarenn has not received any Wall posts.'
        apage += '</p><h6>Fakebook is run by <a href="http://www.ccs.neu.edu/home/choffnes/">David Choffnes</a> at                        '
        apage += "<h2 class='secret_flag' style='color:red'>FLAG: 64-characters-of-random-alphanumerics</h2>"
        apage += '<a href="http://www.northeastern.edu">NEU</a>. It is meant for educational purposes only.                       '
        apage += 'For questions, contact <a href="mailto:choffnes@ccs.neu.edu">David Choffnes</a></h6></body></html>'

        if self.search_secret_flag(apage):
            print self.secret_flag



        # testurl = 'http://cs5700sp15.ccs.neu.edu/fakebook/fakebook/523093905/'
        # print self.try_get(testurl)


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



def test():
    mrl = Myurllib()
    url = 'http://cs5700sp15.ccs.neu.edu/accounts/login/'
    url1 = 'http://cs5700sp15.ccs.neu.edu/fakebook/'
    # print mrl.http_get_url(url)
    # page_content = mrl.GET(url)
    # page_content = mrl.POST(url)
    # urls = re.findall(r'href=[\'"]?([^\'" >]+)', page_content)
    new_page = mrl.GET(url1)
    # setcookies = re.findall(r'Set-Cookie: *([^;]+)', page_content)
    # name = []
    # value = []
    # for i in range(len(setcookies)):
    #     name.append(setcookies[i][0:9])
    #     value.append(setcookies[i][10:len(setcookies[i])])
    #     # print setcookies[i]
    # # mrl.setcookies()
    # for i in range(len(setcookies)):
    #     mrl.set_cookies(name[i], value[i])
    # print name
    # print value
    # print ', '.join(urls)
    # print setcookies



# test()

# s = 'Cookie: csrftoken=8946c93345376143a7cf462c3faffc60; sessionid=8bf35910570ab1ac9b27a510d6cbf5cf\r\n\r\n'

# c = Cookie.SimpleCookie()
# c.load(s)
# print c.output(header="Cookie:")
# m = Myurllib()
# url0 = 'http://cs5700sp15.ccs.neu.edu/accounts/login/'
# paras = {"username":"001710157", "password":"Y83VV8X1", "csrfmiddlewaretoken":"e7ef0edc0cdfffa4bc01857e779fb60c", "next":""}
# cnt = m.POST(url0, paras)
# m.update_cookies(cnt)
# print(m.login_cookie_header())
# print (m.get_paras_header(paras))

# mc = mycrawler()
# mc.login()
# mc.crawl_fakebook()
# print mc.try_get(mc.data_url)


# pages = ''
# pages += '<html><head><title>Fakebook</title><style TYPE="text/css"><!--'

# pages += '#pagelist li { display: inline; padding-right: 10px; }'

# pages += '--></style></head><body><h1>Fakebook</h1><p><a href="/fakebook/">Home</a></p><hr/><h1><a href="/fakebook/519665189/">Rimujuvo Plarenn</a></h1><h2 class=' + 'secret_flag'  + 'style="color:red">FLAG: dd081ed42e6de6617415d1941c99f8b25582b2abb38fe417faf4f274b3323304</h2><h2>Basic Information</h2><ul><li>Sex: Female</li><li>Hometown: Waltham</li></ul><h2>Personal Information</h2><ul></ul><h2>Friends</h2><p><a href="/fakebook/519665189/friends/1/">View Rimujuvo Plarenn' + 's friends</a></p><h2>Wall</h2><p>'

# pages += 'Rimujuvo Plarenn has not received any Wall posts.'

# pages += '</p><h6>Fakebook is run by <a href="http://www.ccs.neu.edu/home/choffnes/">David Choffnes</a> at '

# pages += '<a href="http://www.northeastern.edu">NEU</a>. It is meant for educational purposes only. '

# pages += 'For questions, contact <a href="mailto:choffnes@ccs.neu.edu">David Choffnes</a></h6></body></html>'




# page = mc.try_get('http://david.choffnes.com/classes/cs4700sp15/project2.php')
# print page
# mc.search_secret_flag(pages, '11')

# print mc.secret_flag


# print len('http://cs5700sp15.ccs.neu.edu')
# print 'http://cs5700sp15.ccs.neu.edu/fakebook/974553375/friends/1/'[29:]

# mc = mycrawler()
# mc.search_secret_flag(pages, "rrr")
# for l in mc.secret_flag:
#     print l
# mc.login()



# def main():

# s = 'HTTP/1.1 200 OK'
# ss = re.findall(r'HTTP/1.1 (.*?) OK', s)

# if len(ss) > 0 :
#     print ss[0]


