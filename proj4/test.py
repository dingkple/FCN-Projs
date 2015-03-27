import urlparse
import socket
import sys


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

f1 = open('2MB.log', 'rb')
fl = f1.readlines()
f1.close()

f1 = open('2MB.log.1', 'rb')
fl2 = f1.readlines()
f1.close()

for i in range(len(fl)):
	if fl[i] != fl2[i]:
		print i
		break
		
try:
    recv_sockraw = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
    recv_sockraw.settimeout(0.1)
except socket.error , msg:
    print 'recv error'
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

try:
	recv_sockraw.recvfrom(65536)
except socket.timeout, mag:
	print 'timeout'