import socket
import urlparse
import os
import re
import time
import htmlentitydefs

class Myurllib:

    def __init__(self):
        self.cookies = {}

    def set_cookies(self, name, value):
        self.cookies[name] = value

    def http_get_url(self, url):
        tcpsoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpsoc.bind((url, 80))
        tcpsoc.send('HTTP REQUEST')
        res = tcpsoc.revc(1024)
        return res


    def recv_timeout(self, sock,timeout=0.5):
        #make socket non blocking
        sock.setblocking(0)
         
        #total data partwise in an array
        total_data=[];
        data='';
         
        #beginning time
        begin=time.time()
        while 1:
            #if you got some data, then break after timeout
            if total_data and time.time()-begin > timeout:
                break
             
            #if you got no data at all, wait a little longer, twice the timeout
            elif time.time() - begin > timeout*2:
                break
             
            #recv something
            try:
                data = sock.recv(8192)
                if data:
                    total_data.append(data)
                    #change the beginning time for measurement
                    begin=time.time()
                else:
                    #sleep for sometime to indicate a gap
                    time.sleep(0.1)
            except:
                pass
         
        #join all parts to make final string
        return ''.join(total_data)

    def update_cookies(self, page):
        # print "updating cookies"
        new_cookies = re.findall(r'Set-Cookie: *([^;]+)', page)
        # print new_cookies
        # print self.cookies
        names = []
        values = []
        for i in range(len(new_cookies)):
            names.append(new_cookies[i][0:9])
            values.append(new_cookies[i][10:len(new_cookies[i])])
            self.cookies[names[i]] = values[i]


    def login_cookie_header(self):
        cookies = "Cookie: "
        n = 0
        num_cookies = len(self.cookies.keys())
        for key in self.cookies.keys():
            n+=1
            cookies += key + "="
            cookies += self.cookies[key]
            if n < num_cookies:
                cookies += "; "
        return cookies+"\r\n"


    def get_cookie_header(self):
        cookies = "Cookie: "
        cookies += "sessionid=" + self.cookies['sessionid']
        return cookies+"\r\n"


    def get_statues_code(self, page):
        status = re.findall(r'HTTP/1.1 (.*?) OK', page)
        if len(status) > 0:
            return status[0]
        else:
            return -1

    def GET(self, url):
        data = ''
        try:
            url = urlparse.urlparse(url)
            # print url
            path = url.path
            if path == "":
                path = "/"
            HOST = url.netloc  # The remote host
            PORT = 80          # The same port as used by the server
            # create an INET, STREAMing socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            """
            ***********************************************************************************
            * Note that the connect() operation is subject to the timeout setting,
            * and in general it is recommended to call settimeout() before calling connect()
            * or pass a timeout parameter to create_connection().
            * The system network stack may return a connection timeout error of its own
            * regardless of any Python socket timeout setting.
            ***********************************************************************************
            """
            s.settimeout(0.80)
            """
            **************************************************************************************
            * Avoid socket.error: [Errno 98] Address already in use exception
            * The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
            * without waiting for its natural timeout to expire.
            **************************************************************************************
            """
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #s.setblocking(0)
            s.connect((HOST, PORT))
            # print "GET" + HOST
            # testpost = 'GET /fakebook/ HTTP/1.0\r\n'
            testpost = 'GET %s HTTP/1.0\r\n' % (url.path)
            # testpost += 'Host: cs5700sp15.ccs.neu.edu\r\n'
            testpost += 'Connection: keep-alive\r\n'
            testpost += 'Cache-Control: max-age=0\r\n'
            testpost += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
            # testpost += 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.43 Safari/537.36\r\n'
            # testpost += 'Referer: http://cs5700sp15.ccs.neu.edu/accounts/login/?next=/fakebook/\r\n'
            # testpost += 'Accept-Encoding: gzip, deflate, sdch\r\n'
            testpost += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
            # testpost += 'Cookie: csrftoken=8946c93345376143a7cf462c3faffc60; sessionid=8bf35910570ab1ac9b27a510d6cbf5cf\r\n\r\n'
            if len(self.cookies) > 0:
                testpost += self.login_cookie_header()
            testpost += "\r\n"


            if HOST == 'cs5700sp15.ccs.neu.edu':
                s.send(testpost)
            else:
                header = 'GET http://david.choffnes.com/classes/cs4700sp15/project2.php\r\n'
                header += 'Accept: */*\r\n'
                header += 'Accept-Encoding: gzip, deflate\r\n'
                header += 'User-Agent: runscope/0.1\r\n'
                header += '\r\n'

                print header
                s.send(header)

            # print "GET"
            # print testpost
            # s.send("GET %s HTTP/1.0%s" % (path, CRLF))
            # s.send(testpost)
            # s.send("GET / HTTP/1.0%s" % (CRLF))
            # data = (s.recv(1000000))
            data = self.recv_timeout(s)
            # print data
            # print len(data)
            # https://docs.python.org/2/howto/sockets.html#disconnecting
            s.shutdown(1)
            s.close()
            # print 'Received', repr(data)

            # if self.get_statues_code(data) == "302":

        finally:
            return data


    def get_paras_header(self, parameters = None):
        # return "\r\nusername=%s&password=%s&csrfmiddlewaretoken=%s&next=\r\n\r\n" % (username, password, self.cookies['csrftoken'])
        if parameters is None:
            return None
        # paras = '\r\n'
        # paras = "\r\n"
        # for i in range(len(parameters.keys())):
        #     paras += str(parameters.keys()[i])
        #     paras += "=" 
        #     paras += str(parameters.values()[i])
        #     if i < len(parameters.keys())-1:
        #         paras += "&"
        paras = '\r\nusername=%s&password=%s&csrfmiddlewaretoken=%s&next=' % (parameters['username'], parameters['password'], parameters['csrfmiddlewaretoken'])
        # paras += '%2Ffakebook%2F'
        return paras + "\r\n\r\n"


    def POST(self, url, parameters = None):
        url = urlparse.urlparse(url)
        # print url
        path = url.path
        if path == "":
            path = "/"
        HOST = url.netloc  # The remote host
        PORT = 80          # The same port as used by the server
        # create an INET, STREAMing socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        """
        ***********************************************************************************
        * Note that the connect() operation is subject to the timeout setting,
        * and in general it is recommended to call settimeout() before calling connect()
        * or pass a timeout parameter to create_connection().
        * The system network stack may return a connection timeout error of its own
        * regardless of any Python socket timeout setting.
        ***********************************************************************************
        """
        s.settimeout(0.30)
        """
        **************************************************************************************
        * Avoid socket.error: [Errno 98] Address already in use exception
        * The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state,
        * without waiting for its natural timeout to expire.
        **************************************************************************************
        """
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #s.setblocking(0)
        print "POST" + HOST
        s.connect((HOST, PORT))
        testpost = 'POST %s HTTP/1.0\r\n' % (url.path)
        # testpost += 'Host: cs5700sp15.ccs.neu.edu\r\n'
        testpost += 'Connection: keep-alive\r\n'
        testpost += 'Content-Length: 95\r\n'
        testpost += 'Cache-Control: max-age=0\r\n'
        testpost += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
        testpost += 'Origin: http://cs5700sp15.ccs.neu.edu\r\n'
        testpost += 'User-Agent: HTTPTool/1.0\r\n'
        testpost += 'Content-Type: application/x-www-form-urlencoded\r\n'
        # testpost += 'Accept-Encoding: utf-8, gzip, deflate\r\n'
        testpost += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
        if len(self.cookies.keys()) > 0:
            testpost += self.login_cookie_header()
        # testpost += 'Cookie: csrftoken=8946c93345376143a7cf462c3faffc60; sessionid=36bb12a3559aad527108c21e499170e1\r\n'
        # testpost += 'Cookie: csrftoken=dd981466121a9b3059051770cb9216a2; sessionid=5b1fe2fe734c4e633f7259fad47c8fce\r\n\r\n'
        if parameters is not None:
            testpost += self.get_paras_header(parameters)
        # testpost += 'username=001710157&password=Y83VV8X1&csrftoken=dd981466121a9b3059051770cb9216a2&next=\r\n\r\n'


        # print info
        # print "****************************************"
        # s.send(info)

        # print testpost
        s.send(testpost)
        data = self.recv_timeout(s)
        # print data
        # https://docs.python.org/2/howto/sockets.html#disconnecting
        s.shutdown(1)
        s.close()
        # print 'Received', repr(data)
        return data
