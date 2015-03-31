'''
    Raw sockets on Linux
     
    Silver Moon (m00n.silv3r@gmail.com)
'''
 
# some imports
import socket
import socket
from struct import *
import commands
import random
import urlparse


CSEQ_NUM = 0
SSEQ_NUM = 0
CACK_NUM = 0
SACK_NUM = 0

SRC_PORT = 32354   # source port


data_recvd = {}



def decodeIpHeader(packet):
    mapRet = {}
    mapRet["version"] = (int(ord(packet[0])) & 0xF0)>>4
    mapRet["headerLen"] = (int(ord(packet[0])) & 0x0F)<<2
    mapRet["serviceType"] = hex(int(ord(packet[1])))
    mapRet["totalLen"] = (int(ord(packet[2])<<8))+(int(ord(packet[3])))
    mapRet["identification"] = (int( ord(packet[4])>>8 )) + (int( ord(packet[5])))
    mapRet["id"] = int(ord(packet[6]) & 0xE0)>>5
    mapRet["fragOff"] = int(ord(packet[6]) & 0x1F)<<8 + int(ord(packet[7]))
    mapRet["ttl"] = int(ord(packet[8]))
    mapRet["protocol"] = int(ord(packet[9]))
    mapRet["checkSum"] = int(ord(packet[10])<<8)+int(ord(packet[11]))
    mapRet["srcaddr"] = "%d.%d.%d.%d" % (int(ord(packet[12])),int(ord(packet[13])),int(ord(packet[14])), int(ord(packet[15])))
    mapRet["dstaddr"] = "%d.%d.%d.%d" % (int(ord(packet[16])),int(ord(packet[17])),int(ord(packet[18])), int(ord(packet[19])))
    return mapRet


def decode_tcp_header(packet, mapRet):
    mapRet['src_port'] = (int(ord(packet[0])<<8)) + (int(ord(packet[1])))
    mapRet['dst_port'] = (int(ord(packet[2])<<8)) + (int(ord(packet[3])))
    mapRet['seq_num'] = (long(ord(packet[4])<<24)) + (long(ord(packet[5])<<16))
    mapRet['seq_num'] = mapRet.get('seq_num') + (long(ord(packet[6])<<8)) + (long(ord(packet[7])))
    mapRet['ack_num'] = (long(ord(packet[8])<<24)) + (long(ord(packet[9])<<16))
    mapRet['ack_num'] = mapRet.get('ack_num') + (long(ord(packet[10])<<8)) + (long(ord(packet[11])))
    # mapRet['ack'] = mapRet.get('ack_num') - SEQ_NUM
    mapRet['data_offset'] = (int(ord(packet[12])<<4))
    mapRet['flags'] = 
    mapRet['ns'] = (int(ord(packet[12]) & int('00000001', 2)))
    mapRet['cwr'] = (int(ord(packet[13]) & int('10000000', 2)))>>7
    mapRet['ece'] = (int(ord(packet[13]) & int('01000000', 2)))>>6
    mapRet['urg'] = (int(ord(packet[13]) & int('00100000', 2)))>>5
    mapRet['ack'] = (int(ord(packet[13]) & int('00010000', 2)))>>4
    mapRet['psh'] = (int(ord(packet[13]) & int('00001000', 2)))>>3
    mapRet['rst'] = (int(ord(packet[13]) & int('00000100', 2)))>>2
    mapRet['syn'] = (int(ord(packet[13]) & int('00000010', 2)))>>1
    mapRet['fin'] = (int(ord(packet[13]) & int('00000001', 2)))
    mapRet['window_size'] = (int(ord(packet[14])<<8)) + (int(ord(packet[15])))
    mapRet['checksum'] = (int(ord(packet[16])<<8)) + (int(ord(packet[17])))
    mapRet['urg_pointer'] = (int(ord(packet[18])<<8)) + (int(ord(packet[19])))
    return mapRet
# checksum functions needed for calculation checksum
def checksum(msg):
    s = 0
    # loop taking 2 characters at a time
    # print len(msg)
    for i in range(0, len(msg), 2):
        # print i
        w = ord(msg[i]) + (ord(msg[i+1]) << 8 )
        s = s + w
    s = (s>>16) + (s & 0xffff);
    s = s + (s >> 16);
    #complement and mask to 4 byte short
    s = ~s & 0xffff
    return s


class raw_socket():
    def __init__(self, url):
        random.seed()
        self.url = url
        self.seq_num = 0
        self.ack_num = 0
        self.ip_ihl = 5 
        self.ip_ver = 4
        self.ip_tos = 0
        self.ip_tot_len = 0  # kernel will fill the correct total length
        self.ip_id = random.randint(0, 1<<15)
        self.ip_frag_off = 0
        self.ip_ttl = 255
        self.ip_proto = socket.IPPROTO_TCP
        self.ip_check = 0    # kernel will fill the correct checksum
  
        self.ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl
        self.tcp_dest = 80   # destination port
        self.tcp_seq = 0
        self.tcp_ack_seq = 0
        self.tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        #tcp flags
        self.tcp_fin = 0
        self.tcp_syn = 0
        self.tcp_rst = 0
        self.tcp_psh = 0
        self.tcp_ack = 0
        self.tcp_urg = 0
        self.tcp_window = socket.htons(5840)    #   maximum allowed window size
        self.tcp_check = 0
        self.tcp_urg_ptr = 0
        self.tcp_offset_res = (self.tcp_doff << 4) + 0
        self.flags = 0

        self.sack = 0
        self.sseq = 0

        self.sock = None

        self.isConnected = False
        self.buffer = ''
        self.MSS = 1460

        self.source_ip = ''
        self.dest_ip = ''
        self.src_port = random.randint(30000, 60000)

        self.analyze_dest()
        self.get_local_ip_addr()
        self.ip_saddr = socket.inet_aton ( self.source_ip )   #Spoof the source ip address if you want to
        self.ip_daddr = socket.inet_aton ( self.dest_ip ) 

    def analyze_dest(self):
        url = urlparse.urlparse(self.url)
        self.dest_ip = socket.gethostbyname(url.netloc)

    def get_local_ip_addr(self):
        ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                             "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
        for ip in ips.split():
            if ip[:3] != '127':
                self.source_ip = ip
                return
        self.source_ip = ''
 
#create a raw socket    

    def create_sock(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
            self.sock.bind(('0.0.0.0', self.src_port))
        except socket.error, msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()

    def construct_ip_header(self):
        self.ip_id += 1
        print 'raw_class: '
        print self.dest_ip
        print self.source_ip
        #Spoof the source ip address if you want to
        # self.ip_saddr = socket.inet_aton(self.source_ip)   
        # self.ip_daddr = socket.inet_aton(self.dest_ip)      
        # the ! in the pack format string means network order
        print self.ip_ihl_ver
        print self.ip_tos
        print self.ip_tot_len
        print self.ip_id
        print self.ip_frag_off
        print self.ip_ttl
        print self.ip_proto
        print self.ip_check
        print self.ip_saddr
        print self.ip_daddr
        ip_header = pack('!BBHHHBBH4s4s', self.ip_ihl_ver, self.ip_tos, self.ip_tot_len, self.ip_id, self.ip_frag_off, 
            self.ip_ttl, self.ip_proto, self.ip_check, self.ip_saddr, self.ip_daddr)
        return ip_header


    def hand_shake(self):
        print 'hand_shaking: '
        # try:
        #     s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        # except socket.error, msg:
        #     print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        #     sys.exit()
        self.create_sock()
        packet = self.construct_packets('syn')
        print self.dest_ip
        self.sock.sendto(packet, (self.dest_ip, 0))    # put this in a loop if you want to flood the target 
        response = self.recive_packets()
        if (response.has_key('syn') and response.get('syn') == 1 and 
            response.has_key('ack') and response.get('ack') == 1):
            print 'acking with CSEQ: ' + str(CSEQ_NUM)
            packet = construct_packets('ack')
            self.sock.sendto(packet, (dest_ip , 0))    
            # response = recive_packets(source_ip, dest_ip)
            self.isConnected  = True


    def construct_packets(self, ptype):
        print 'constructing: ' + ptype
        ip_header = self.construct_ip_header()
        if ptype == 'syn':
            self.tcp_seq = random.randint(0, 65536)
            self.tcp_ack = 0
            self.tcp_syn = 1
        elif ptype == 'ack_syn':
            self.tcp_ack = 1
            self.tcp_ack_seq = self.sseq + 1
            self.tcp_seq = self.sack
        elif ptype == 'get':
            self.tcp_psh = 1
            self.tcp_ack = 1
            self.tcp_seq = self.sack
            self.tcp_ack_seq = self.sseq
        elif ptype == 'ack':
            self.tcp_ack = 1
            self.tcp_seq = self.sack
            self.tcp_ack_seq = self.sseq
        self.tcp_flags = self.tcp_fin + (self.tcp_syn << 1) + (self.tcp_rst << 2) + (self.tcp_psh <<3) + (self.tcp_ack << 4) + (self.tcp_urg << 5)
        print self.src_port
        tcp_header = pack('!HHLLBBHHH', self.src_port, self.tcp_dest, self.tcp_seq, self.tcp_ack_seq, self.tcp_offset_res, self.tcp_flags, self.tcp_window, self.tcp_check, self.tcp_urg_ptr)
        source_address = socket.inet_aton(self.source_ip)
        dest_address = socket.inet_aton(self.dest_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        user_data = self.get_data()
        if len(user_data) % 2 != 0:
            user_data = user_data + ' '
        tcp_length = len(tcp_header) + len(user_data)
        psh = pack('!4s4sBBH', source_address, dest_address , placeholder , protocol , tcp_length)
        psh = psh + tcp_header + user_data;
        # print psh
        
        tcp_check = checksum(psh)
        #print tcp_checksum
        # make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
        tcp_header = pack('!HHLLBBH' , self.src_port, self.tcp_dest, self.tcp_seq, self.tcp_ack_seq, self.tcp_offset_res, self.tcp_flags, self. tcp_window) + pack('H' , tcp_check) + pack('!H' , self.tcp_urg_ptr)
        if ptype == 'get':
            packet = ip_header + tcp_header + user_data
        else:
            packet = ip_header + tcp_header
        print 'ip_header: ' + str(ip_header) + ' ' + str(len(ip_header))
        print 'tcp_header: ' + str(tcp_header) + ' ' + str(len(tcp_header))
        print 'userdata: ' + str(user_data) + ' ' + str(len(user_data))
        return packet

    def get_data(self):
        if len(self.buffer) > self.MSS:
            data = self.buffer[:self.MSS]
            self.buffer = self.buffer[self.MSS:]
        else:
            data = self.buffer
            self.buffer = ''
        return data

    def recive_packets(self):
        print 'rcving: '
        while True:
            print 'getting_packets: '
            try:
                # s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                # s.settimeout(2)
                # print self.src_port
                # s.bind(('0.0.0.0', self.src_port))
                received_packet = self.sock.recvfrom(65536)
                print 'rcved'
                #packet string from tuple
                received_packet = received_packet[0]
                ip_header = received_packet[0:20]
                tcp_header = received_packet[20:40]
                #now unpack them
                iph = unpack('!BBHHHBBH4s4s' , ip_header)
                if len(iph) > 0:
                    print iph
                    mapIpTmp = decodeIpHeader(ip_header)
                    mapIpTmp = decode_tcp_header(tcp_header, mapIpTmp)
                    for k,v in mapIpTmp.items():
                        print k,"\t:\t",v
                    print '******************************************'
                    # print str(mapIpTmp.get('dst_port')) + str(mapIpTmp.get('dst_port') == SRC_PORT)
                    # print str(mapIpTmp.get('srcaddr')) + str(mapIpTmp.get('src_port') == dest_ip) + dest_ip
                    # print str(mapIpTmp.get('dstaddr')) + str(mapIpTmp.get('dstaddr') == source_ip)
                    if (mapIpTmp.has_key('dst_port') and mapIpTmp.get('dst_port') == self.src_port
                        and mapIpTmp.has_key('srcaddr') and mapIpTmp.get('srcaddr') == dest_ip
                        and mapIpTmp.has_key('dstaddr') and mapIpTmp.get('dstaddr') == source_ip):
                        mapIpTmp['data'] = received_packet[40:]
                        return mapIpTmp
            except socket.error, msg:
                # print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                print msg
                # sys.exit()
            

    def test_get_ulr(self):
        self.hand_shake()
        if self.isConnected:
            self.buffer += get_test_header()
            packet = self.construct_packets('get')
            self.send_packet(packet)
            response = self.recive_packets()
            while response.get('fin') != 1 and len(response.get('data')) > 0:
                packet = self.construct_packets('ack')
                response = self.recive_packets(packet)
                self.send_packet(packet)
            # if response.get('fin') != 1 and len(response.get('data')) == 0:
            #     packet = self.construct_packets('fin_acy')
            #     self.send_packet(packet)
            # elif 


    def send_packet(self, packet):
        self.create_sock()
        self.sock.sendto(packet, (self.dest_ip, 0))


# tell kernel not to put in headers, since we are providing it, when using IPPROTO_RAW this is not necessary
# s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
 
# ip header fields


def get_local_ip_addr():
    ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                         "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
    for ip in ips.split():
        if ip[:3] != '127':
            source_ip = ip
            return ip
    self.source_ip = ''

def construct_ip_header(source_ip, dest_ip):
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    ip_tot_len = 0  # kernel will fill the correct total length
    ip_id = 54321   #Id of this packet
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_TCP
    ip_check = 0    # kernel will fill the correct checksum
    ip_saddr = socket.inet_aton ( source_ip )   #Spoof the source ip address if you want to
    ip_daddr = socket.inet_aton ( dest_ip )
     
    ip_ihl_ver = (ip_ver << 4) + ip_ihl

    print 'fucntion:'
    print ip_ihl 
    print ip_ver 
    print ip_tos 
    print ip_tot_len 
    print ip_id 
    print ip_frag_off 
    print ip_ttl 
    print ip_proto 
    print ip_check 
    print ip_saddr 
    print ip_daddr 
     
    print ip_ihl_ver
     
    # the ! in the pack format string means network order
    ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
    return ip_header


def construct_packet(source_ip, dest_ip, user_data, seq, ack, ptype):
    global CSEQ_NUM
    global SSEQ_NUM
    ip_header = construct_ip_header(source_ip, dest_ip)
    # tcp header fields
    tcp_dest = 80   # destination port
    if ptype == 'syn':
        tcp_seq = seq
        CSEQ_NUM = tcp_seq
        print 'cseq: ' + str(CSEQ_NUM)
        tcp_ack_seq = ack
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        #tcp flags
        tcp_fin = 0
        tcp_syn = 1
        tcp_rst = 0
        tcp_psh = 0
        tcp_ack = 0
        tcp_urg = 0
    elif ptype == 'ack':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        tcp_seq = seq + 1
        CSEQ_NUM = tcp_seq
        tcp_ack_seq = ack + 1
        SSEQ_NUM = tcp_ack_seq
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        #tcp flags
        tcp_fin = 0
        tcp_syn = 0
        tcp_rst = 0
        tcp_psh = 0
        tcp_ack = 1
        tcp_urg = 0
    elif ptype == 'get':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        tcp_seq = seq
        tcp_ack_seq = ack 
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        #tcp flags
        tcp_fin = 0
        tcp_syn = 0
        tcp_rst = 0
        tcp_psh = 1
        tcp_ack = 1
        tcp_urg = 0
    tcp_window = socket.htons(5840)    #   maximum allowed window size
    tcp_check = 0
    tcp_urg_ptr = 0
     
    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
    # the ! in the pack format string means network order
    tcp_header = pack('!HHLLBBHHH', SRC_PORT, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
    source_address = socket.inet_aton( source_ip )
    dest_address = socket.inet_aton(dest_ip)
    placeholder = 0
    protocol = socket.IPPROTO_TCP
    tcp_length = len(tcp_header) + len(user_data)
    psh = pack('!4s4sBBH', source_address, dest_address , placeholder , protocol , tcp_length)
    psh = psh + tcp_header + user_data;
    # print psh
    if len(psh) % 2 != 0:
        psh = psh + ' '
    tcp_check = checksum(psh)
    #print tcp_checksum
    # make the tcp header again and fill the correct checksum - remember checksum is NOT in network byte order
    tcp_header = pack('!HHLLBBH' , SRC_PORT, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
    packet = ip_header + tcp_header + user_data
    print 'ip_header: ' + str(ip_header) + ' ' + str(len(ip_header))
    print 'tcp_header: ' + str(tcp_header) + ' ' + str(len(tcp_header))
    print 'userdata: ' + str(user_data) + ' ' + str(len(user_data))
    return packet


def hand_shake(source_ip, dest_ip):
    global SSEQ_NUM
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    except socket.error, msg:
        print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    packet = construct_packet(source_ip, dest_ip, '', random.randint(0, 65536), 0, 'syn')
    s.sendto(packet, (dest_ip , 0))    # put this in a loop if you want to flood the target 
    response = recive_packets(source_ip, dest_ip)
    if (response.has_key('syn') and response.get('syn') == 1 and 
        response.has_key('ack') and response.get('ack') == 1):
        SSEQ_NUM = response.get('seq_num')
        print 'acking with CSEQ: ' + str(CSEQ_NUM)
        packet = construct_packet(source_ip, dest_ip, '', CSEQ_NUM, SSEQ_NUM, 'ack')
        s.sendto(packet, (dest_ip , 0))    # put this in a loop if you want to flood the target
        # response = recive_packets(source_ip, dest_ip)
    return True


def send_to_dest(source_ip, dest_ip, user_data):
    if hand_shake(source_ip, dest_ip):
        print 'finished hand_shake'

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        except socket.error, msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()     
        # final full packet - syn packets dont have any data
        user_data = get_test_header()
        packet = construct_packet(source_ip, dest_ip, user_data, CSEQ_NUM, SSEQ_NUM, 'get')
        s.sendto(packet, (dest_ip, 0))
        response = recive_packets(source_ip, dest_ip)
        # Send the packet finally - the port specified has no effect


def recive_packets(source_ip, dest_ip):
    while True:
        try:
            recv_sockraw = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        except socket.error , msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
        received_packet = recv_sockraw.recvfrom(65536)
       
        #packet string from tuple
        received_packet = received_packet[0]
        ip_header = received_packet[0:20]
        tcp_header = received_packet[20:40]
        #now unpack them
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
        if len(iph) > 0:
            print iph
            mapIpTmp = decodeIpHeader(ip_header)
            mapIpTmp = decode_tcp_header(tcp_header, mapIpTmp)
            for k,v in mapIpTmp.items():
                print k,"\t:\t",v
            print '******************************************'
            # print str(mapIpTmp.get('dst_port')) + str(mapIpTmp.get('dst_port') == src_port)
            # print str(mapIpTmp.get('srcaddr')) + str(mapIpTmp.get('src_port') == dest_ip) + dest_ip
            # print str(mapIpTmp.get('dstaddr')) + str(mapIpTmp.get('dstaddr') == source_ip)
            if (mapIpTmp.has_key('dst_port') and mapIpTmp.get('dst_port') == SRC_PORT
                and mapIpTmp.has_key('srcaddr') and mapIpTmp.get('srcaddr') == dest_ip
                and mapIpTmp.has_key('dstaddr') and mapIpTmp.get('dstaddr') == source_ip):
                return mapIpTmp

def get_test_header():
        # user_data = 'Hello, how are you'
    user_data = 'GET / HTTP/1.1\n'
    user_data += 'Host: david.choffnes.com\n'
    # user_data += 'Connection: keep-alive\n'
    user_data += 'Cache-Control: max-age=0\n'
    user_data += 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\n'
    # user_data += 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.50 Safari/537.36\n'
    user_data += 'Accept-Encoding: gzip, deflate, sdch\n'
    user_data += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\n'
    # user_data += 'Cookie: __utmt=1; __utma=135809699.1247664866.1423368106.1425909828.1427059822.11; __utmb=135809699.4.10.1427059822; __utmc=135809699; __utmz=135809699.1423368106.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)\n'
    user_data += '\n'
    user_data += '\n'

    # user_data = ''
    return user_data


def main():
    # now start constructing the packet
    packet = ''
    source_ip = get_local_ip_addr()
    if source_ip == '':
        print 'can not get ip_addr'
        exit(1)
    print 'source_ip ' + source_ip
    # dest_ip = '192.168.1.1' # or socket.gethostbyname('www.google.com')
    dest_ip = socket.gethostbyname('david.choffnes.com')
    print 'dest_ip ' + dest_ip
    user_data = get_test_header()
    send_to_dest(source_ip, dest_ip, user_data)
    # recive_packets()

# main()


if __name__ == '__main__':
    rs = raw_socket('http://david.choffnes.com')
    rs.test_get_ulr()












