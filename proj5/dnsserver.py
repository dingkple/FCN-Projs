import sys
import struct
import socket
import SocketServer
import json

DEFAULT_REPLICA = '52.4.98.110'
DEBUG = True


class MyDNSPacket():
    def __init__(self):
        self.id = 0
        self.flags = 0
        self.qst_num = 0
        self.ans_num = 0
        self.authRR_num = 0
        self.addiRR_num = 0

        #these too var's initial value is not important since they r initialized
        #when unpacking incoming packets
        self.q_type = 0
        self.q_class = 0
        self.q_name = ''


    def construct_packet(self, ip):
        self.ans_num = 1
        self.flags = 0x8180

        header = struct.pack(
            '>HHHHHH', 
            self.id, 
            self.flags, 
            self.qst_num, 
            self.ans_num, 
            self.authRR_num, 
            self.addiRR_num)

        query = ''.join(chr(len(k)) + k for k in self.q_name.split('.'))
        query += '\x00'  # add end symbol
        query_part =  query + struct.pack('>HH', self.q_type, self.q_class)

        an_name = 0xC00C
        an_type = 0x0001
        an_class = 0x0001
        an_ttl = 60  # time to live
        an_len = 4
        answer_part = struct.pack('>HHHLH4s', an_name, an_type, an_class,
                          an_ttl, an_len, socket.inet_aton( ip ));

        packet = header + query_part + answer_part

        return packet

    def unpack_packet(self, data):
        [self.id,
        self.flags,
        self.qst_num,
        self.ans_num,
        self.authRR_num,
        self.addiRR_num] = struct.unpack('>HHHHHH', data[:12])

        query_data = data[12:]
        [self.q_type, self.q_class] = struct.unpack('>HH', query_data[-4:])
        s = query_data[:-4]
        self.q_name = self.__resolve_q_name(s)
        

    def __resolve_q_name(self, data):
        res = ''
        ptr = 0
        qst_content = []
        if DEBUG:
            print 'before resolved: ',
            print str(data)
        try :
            while True:
                part_len = ord(data[ptr])
                if part_len == 0:
                    break
                ptr += 1
                qst_content.append(data[ptr:ptr + part_len])
                ptr += part_len
            res = '.'.join(qst_content)
        except:
            res = 'cs5700cdn.example.com'
        if DEBUG:
            print 'q_name_resolved: ',
            print res
        return res


class MyDNSRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        if DEBUG:
            print 'handling requests:'
        data = self.request[0]
        sock = self.request[1]

        packet = MyDNSPacket()
        packet.unpack_packet(data)
        
        if packet.q_type == 1 and packet.q_name == self.server.hostname:
            ip = DEFAULT_REPLICA
            response = packet.construct_packet(ip)
            sock.sendto(response, self.client_address)


class MyDNSServer(SocketServer.UDPServer):
    def __init__(self, hostname, server_address, handler_class = MyDNSRequestHandler):
        SocketServer.UDPServer.__init__(self, server_address, handler_class)
        self.hostname = hostname


def main():
    argv = sys.argv
    if len(argv) != 5 or argv[1] != "-p" or argv[3] != "-n":
        sys.exit( "command format error: ./dnsserver -p [port] -n [name]" )
    port = int(argv[2])
    name = argv[4]
    if DEBUG:
        print name,
        print port
    dns_server = MyDNSServer(name, ('', port))
    dns_server.serve_forever()

if __name__ == '__main__':
    main()







