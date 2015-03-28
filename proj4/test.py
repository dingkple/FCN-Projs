import urlparse
import socket
import sys
import re


# a = 'http://david.choffnes.com/classes/cs4700sp15/10MB.log'

# url = urlparse.urlparse(a)
# filename = 'index.html'
# print url.path
# if '/' in url.path:
#     path = url.path.split('/')
#     if path[-1] != '':
#         filename = path[-1]

# print filename
# print a.path.split('/')

# f = open('2MB.log', 'r')
# ls = f.readlines()
# f.close()

# f = open('22.log', 'wb')
# data = ''.join(ls)
# cnt = data.find('\r\n\r\n')
# data = data[cnt+4:]
# f.write(data)
# f.close()

# f1 = open('2MB.log', 'rb')
# fl = f1.readlines()
# f1.close()

# f1 = open('2MB.log.1', 'rb')
# fl2 = f1.readlines()
# f1.close()

# for i in range(len(fl)):
# 	if fl[i] != fl2[i]:
# 		print i
# 		break
		
# try:
#     recv_sockraw = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
#     recv_sockraw.settimeout(0.1)
# except socket.error , msg:
#     print 'recv error'
#     print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
#     sys.exit()

# try:
# 	recv_sockraw.recvfrom(65536)
# except socket.timeout, mag:
# 	print 'timeout'

s = ''
s = 'HTTP/1.1 200 OK\r\n'
s += 'Date: Sat, 28 Mar 2015 03:46:21 GMT\r\n'
s += 'Server: Apache/2.2.24 (Unix) mod_ssl/2.2.24 OpenSSL/0.9.7a mod_auth_passthrough/2.1 mod_bwlimited/1.4 FrontPage/5.0.2.2635 mod_fcgid/2.3.6\r\n'
s += 'Last-Modified: Wed, 23 Jul 2014 14:59:23 GMT\r\n'
s += 'ETag: "8ec024-200000-4fedd95e6c8c0"\r\n'
s += 'Accept-Ranges: bytes\r\n'
s += 'Content-Length: 2097152\r\n'
s += 'Keep-Alive: timeout=5, max=100\r\n'
s += 'Connection: Keep-Alive\r\n'
s += 'Content-Type: text/x-log\r\n'

print s

num = re.match(r'.*?\sContent-Length: ([\d]*)\s.*?', s)

ss = re.search(r'.*?\sContent-Length: ([\d]*)\s.*?', s)

print ss.groups()
