#!/usr/bin/python
import socket
import socket
from struct import *
import commands
import random
import urlparse
import time
import sys
import binascii


BASE_SEQ = 0
CSEQ_NUM = 0
SSEQ_NUM = 0
CACK_NUM = 0
SACK_NUM = 0

SBASE_SEQ = 0

MSS = 1400

IP_ID = 0


NEED_PRINT = False


DATA_RCVD = {}
USER_DATA = ' '
LAST_RCVD_TIME = {}
SENT_PKT ={}
CWD = 1

random.seed()

SRC_MAC = ''
DST_MAC = ''
GATEWAYIP = ''

ALL_PACKS = []


SRC_PORT = random.randint(30000, 60000)   # source port

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


def carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def ip_header_checksum(msg):
    s = 0
    for i in range(0, len(msg), 2):
        w = ord(msg[i]) + (ord(msg[i+1]) << 8)
        s = carry_around_add(s, w)
    return ~s & 0xffff

def get_local_mac_addr():
    # ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'
    ips = commands.getoutput("/sbin/ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'")
    for ip in ips.split():
        if ip[:3] != '127':
            source_ip = ip
            return ip
    self.source_ip = ''

def get_default_gateway_linux():
    """Read the default gateway directly from /proc."""
    with open("/proc/net/route") as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue
            return socket.inet_ntoa(pack("<L", int(fields[2], 16)))

def get_local_ip_addr():
    ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                         "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
    for ip in ips.split():
        if ip[:3] != '127':
            source_ip = ip
            return ip
    self.source_ip = ''


def construct_frame_header():
    print 'coconstruct_frame_headerns: ',
    print SRC_MAC,
    print DST_MAC
    eth_hdr = pack("!6s6s2s", DST_MAC.replace(':', '').decode('hex'), SRC_MAC.replace(':','').decode('hex'), '\x08\x00')  
    # dst_hdr = pack("!6s6s2s", '\xff\xff\xff\xff\xff\xff', dstmac.replace(':', '').decode('hex'), '\x08\x00')

    packet = eth_hdr
    print unpack("!6s6s2s", packet)
    return packet  

def construct_frame_ip_header(source_ip, dest_ip, length):
    global IP_ID
    IP_ID += 1

    frame_header = construct_frame_header()
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    
    #Id of this packet
    ip_id = IP_ID   
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_TCP

    #os will fill the following two field
    ip_tot_len = 20 + length
    ip_check = 0

    ip_saddr = socket.inet_aton (source_ip)   
    ip_daddr = socket.inet_aton (dest_ip)   
    ip_ihl_ver = (ip_ver << 4) + ip_ihl
    ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, 
        ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
    cs = checksum(ip_header)

    ip_check = cs & 0xffff

    ip_header = pack('!BBHHHBB' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, 
        ip_ttl, ip_proto)
    ip_header += pack('H', ip_check) + pack('!4s4s', ip_saddr, ip_daddr) 

    return frame_header + ip_header


# def construct_ip_header(source_ip, dest_ip):
#     ip_ihl = 5
#     ip_ver = 4
#     ip_tos = 0
    
#     #Id of this packet
#     ip_id = 54321   
#     ip_frag_off = 0
#     ip_ttl = 255
#     ip_proto = socket.IPPROTO_TCP

#     #os will fill the following two field
#     ip_tot_len = 0
#     ip_check = 0

#     ip_saddr = socket.inet_aton (source_ip)   
#     ip_daddr = socket.inet_aton (dest_ip)   
#     ip_ihl_ver = (ip_ver << 4) + ip_ihl
#     ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, 
#         ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
#     return ip_header


def construct_packet(source_ip, dest_ip, user_data, seq, ack, ptype, withfin = 0):
    global CSEQ_NUM
    global SSEQ_NUM
    print ptype,
    print seq,
    print ack
    # tcp header fields
    tcp_urg = 0
    tcp_rst = 0
    tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
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
        tcp_psh = 0
        tcp_ack = 0

    elif ptype == 'ack_syn':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        tcp_seq = seq
        CSEQ_NUM = tcp_seq
        tcp_ack_seq = ack
        SSEQ_NUM = tcp_ack_seq
        #tcp flags
        tcp_fin = 0
        tcp_syn = 0
        tcp_psh = 0
        tcp_ack = 1
    elif ptype == 'ack':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        tcp_seq = seq
        tcp_ack_seq = ack
        SSEQ_NUM = tcp_ack_seq
        #tcp flags
        tcp_fin = 0
        tcp_syn = 0
        tcp_psh = 0
        tcp_ack = 1
    elif ptype == 'send':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        print user_data
        tcp_seq = seq
        tcp_ack_seq = ack 
        #tcp flags
        tcp_fin = 0
        tcp_syn = 0
        tcp_psh = 1
        tcp_ack = 1
    elif ptype == 'fin':
        print 'ack with seq: ' + str(seq) + " " + str(ack)
        tcp_seq = seq
        tcp_ack_seq = ack 
        #tcp flags
        tcp_fin = 1
        tcp_syn = 0
        tcp_psh = 0
        tcp_ack = 1
    if withfin == 1:
        tcp_fin = 1
    tcp_window = socket.htons(200)    #   maximum allowed window size
    tcp_check = 0
    tcp_urg_ptr = 0
     
    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
    tcp_header = pack('!HHLLBBHHH', SRC_PORT, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, 
        tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
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
    tcp_header = pack('!HHLLBBH' , SRC_PORT, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) 
    tcp_header += pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
    ip_header = construct_frame_ip_header(source_ip, dest_ip, len(tcp_header) + len(user_data))
    packet = ip_header + tcp_header + user_data
    CSEQ_NUM += len(user_data)
    SENT_PKT[CSEQ_NUM] = [time.time(), user_data, seq, ack]
    return packet


def hand_shake(source_ip, dest_ip):
    global SSEQ_NUM
    global CSEQ_NUM
    global BASE_SEQ
    global IP_ID
    IP_ID = random.randint(10000, 30000)
    try:
        # s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        s.settimeout(180)
    except socket.error, msg:
        print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    CSEQ_NUM = random.randint(0, 65536)
    BASE_SEQ = CSEQ_NUM
    packet = construct_packet(source_ip, dest_ip, '', CSEQ_NUM, 0, 'syn')
    # s.sendto(packet, (dest_ip , 0))    # put this in a loop if you want to flood the target 
    s.bind(('eth0', 0))
    s.send(packet)
    # send_packet(source_ip, dest_ip, packet)
    response = recive_packets(source_ip, dest_ip)
    CACK_NUM = response.get('ack_num')
    if (response.has_key('syn') and response.get('syn') == 1 and 
        response.has_key('ack') and response.get('ack') == 1):
        SSEQ_NUM = response.get('seq_num')
        print 'acking with CSEQ: ' + str(CSEQ_NUM)
        CSEQ_NUM += 1
        SSEQ_NUM += 1
        packet = construct_packet(source_ip, dest_ip, '', CSEQ_NUM, SSEQ_NUM, 'ack_syn')
        # s.sendto(packet, (dest_ip , 0))    # put this in a loop if you want to flood the target
        s.bind(('eth0', 0))
        s.send(packet)
        # send_packet(source_ip, dest_ip, packet)
        # response = recive_packets(source_ip, dest_ip)
    return True

def get_user_data():
    global USER_DATA
    global CSEQ_NUM
    cur_seq = CSEQ_NUM - BASE_SEQ
    available_size = min([CWD * MSS - CACK_NUM, len(USER_DATA) - cur_seq])
    print 'current seq: ' + str(cur_seq)
    print 'fetching data for packet with CSEQ: ' + str(cur_seq)
    print len(USER_DATA),
    print available_size,
    print cur_seq
    current_data = USER_DATA[cur_seq: cur_seq + available_size]
    res = ''
    if len(current_data) > MSS:
        res = current_data[:MSS]
        current_data = current_data[MSS:]
    else:
        res = current_data + ''
        current_data = ''
    print 'length: ' + str(len(res))
    return res


def check_for_retransmit(source_ip, dest_ip):
    cur_t = time.time()
    for seq in SENT_PKT.keys():
        if SENT_PKT.get(seq)[0] - cur_t > 60:
            op = SENT_PKT.get(seq)
            packet = construct_packet(source_ip, dest_ip, op[1], op[2], op[3], 'send')
            try:
                s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
                s.settimeout(180)
            except socket.error, msg:
                print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                sys.exit()
            s.bind(('eth0', 0))
            s.send(packet)


def send_to_dest(url, source_ip, dest_ip):
    global CSEQ_NUM
    global SSEQ_NUM
    global CWD
    if hand_shake(source_ip, dest_ip):
        print 'finished hand_shake'
        try:
            s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            s.settimeout(180)
        except socket.error, msg:
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()     
        # final full packet - syn packets dont have any data
        get_http_header(url)
        data = get_user_data()
        packet = construct_packet(source_ip, dest_ip, data, CSEQ_NUM, SSEQ_NUM, 'send')
        # s.sendto(packet, (dest_ip, 0))
        s.bind(('eth0', 0))
        s.send(packet)
        response = recive_packets(source_ip, dest_ip)
        while True:

            print '##############################'
            # print 'checksum: ' + str(checksum_packet(response))
            if NEED_PRINT:
                print 'Right addr pair: '
            if response.get('ack') == 1:
                temp = response.get('ack_num')
                CACK_NUM = temp
                if SENT_PKT.has_key(temp): 
                    del SENT_PKT[temp]
            check_for_retransmit(source_ip, dest_ip)
            if response.get('ack') == 1 and response.get('psh') == 1:
                CWD += 1
                if len(response.get('data')) > 0:
                    if NEED_PRINT:
                        print 'pushing to buffer and ack: '
                    if response.get('seq_num') not in DATA_RCVD.keys():
                        DATA_RCVD[response.get('seq_num')] = response.get('data')
                    update_ack()
                    if NEED_PRINT:
                        print 'preparing ack: '
                    data = get_user_data()
                    if len(data) > 0:
                        print 'with data: !!!!!!!!!!!! = ' + data
                    if response.get('fin') != 1:
                        packet = construct_packet(source_ip, dest_ip, data, CSEQ_NUM, SSEQ_NUM, 'ack')
                    else:
                        packet = construct_packet(source_ip, dest_ip, data, CSEQ_NUM, SSEQ_NUM, 'ack', withfin = 1)
                    
                    try:
                        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
                        s.settimeout(180)
                    except socket.error, msg:
                        print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                        sys.exit() 
                    s.bind(('eth0', 0))
                    s.send(packet)
            elif response.get('ack') == 1 and response.get('fin') != 1:
                print 'just ack'
                SSEQ_NUM = response.get('seq_num')
                CSEQ_NUM = response.get('ack_num')

            elif len(USER_DATA) > CSEQ_NUM:
                send_user_data(source_ip, dest_ip, response.get('window_size'))

            elif response.get('fin') == 1:
                start_tear_down(source_ip, dest_ip, response.get('seq_num'))
                break
            response = recive_packets(source_ip, dest_ip)
        print 'rcvd wrong packet'

def update_ack():
    global CSEQ_NUM
    global SSEQ_NUM
    temp = SSEQ_NUM
    print ' '.join(map(str, DATA_RCVD.keys()))
    while True:
        if SSEQ_NUM in DATA_RCVD.keys():
            SSEQ_NUM += len(DATA_RCVD.get(SSEQ_NUM))
        else:
            break
    print 'now ack: ' + str(SSEQ_NUM),
    print 'skip from ' + str(temp) + 'to ' + str(SSEQ_NUM)

def send_user_data(source_ip, dest_ip, receiver_adv_win):
    global CSEQ_NUM
    global SSEQ_NUM
    if len(USER_DATA) <= CSEQ_NUM:
        return
    while True:
        data = get_user_data()
        if len(data) > 0:
            packet = construct_packet(source_ip, dest_ip, data, CSEQ_NUM, SSEQ_NUM, 'send')
            try:
                # s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
                s.settimeout(180)
            except socket.error, msg:
                print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
                sys.exit() 
            # s.sendto(packet, (dest_ip, 0))
            s.bind(('eth0', 0))
            s.send(packet)
            num_sent += len(data)

            

def start_tear_down(source_ip, dest_ip, seq):
    print 'tearing down'
    packet = construct_packet(source_ip, dest_ip,'', CSEQ_NUM, seq+1, 'fin')
    try:
        # s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        s.settimeout(180)
    except socket.error, msg:
        print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit() 
    # s.sendto(packet, (dest_ip, 0))
    s.bind(('eth0', 0))
    s.send(packet)



#This func can be improve a lot
def recive_packets(source_ip, dest_ip):
    global LAST_RCVD_TIME
    while True:
        try:
            recv_sockraw = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
            recv_sockraw.settimeout(180)
        except socket.error , msg:
            print 'recv error'
            print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()
        try:
            received_packet = recv_sockraw.recvfrom(65536)
            print 'rcvd: ' + str(time.time())
            LAST_RCVD_TIME = time.time()
        except socket.timeout:
            print 'time out'
            sys.eixt(0)
        #packet string from tuple
        received_packet = received_packet[0]
        # print 'recv length: ' + str(len(received_packet))
        received_packet = received_packet[14:]
        ip_header = received_packet[0:20]
        iph = unpack('!BBHHHBBH4s4s' , ip_header)
        if ip_header_checksum(ip_header) != 0:
            print ip_header_checksum(ip_header)
            continue
        mapIpTmp = decodeIpHeader(ip_header)
        if (mapIpTmp.get('protocol') != socket.IPPROTO_TCP
            or not mapIpTmp.has_key('srcaddr') or not mapIpTmp.get('srcaddr') == dest_ip
            or not mapIpTmp.has_key('dstaddr') or not mapIpTmp.get('dstaddr') == source_ip):
            continue
        tcp_header = received_packet[20:40]
        
        if len(iph) > 0:
            mapIpTmp = decode_tcp_header(tcp_header, mapIpTmp)
            mapIpTmp['data'] = received_packet[40:]
            ALL_PACKS.append(mapIpTmp.get('seq_num'))
            # for k,v in mapIpTmp.items():
            #     print k,"\t:\t",v
            # print '******************************************'
            # print str(mapIpTmp.get('dst_port')) + str(mapIpTmp.get('dst_port') == src_port)
            # print str(mapIpTmp.get('srcaddr')) + str(mapIpTmp.get('src_port') == dest_ip) + dest_ip
            # print str(mapIpTmp.get('dstaddr')) + str(mapIpTmp.get('dstaddr') == source_ip)
            print mapIpTmp.get('dstaddr'),
            print mapIpTmp.get('srcaddr'),
            print mapIpTmp.get('dst_port'),
            print mapIpTmp.get('src_port')
            if (mapIpTmp.has_key('dst_port') and mapIpTmp.get('dst_port') == SRC_PORT
                and mapIpTmp.has_key('srcaddr') and mapIpTmp.get('srcaddr') == dest_ip
                and mapIpTmp.has_key('dstaddr') and mapIpTmp.get('dstaddr') == source_ip):
                return mapIpTmp



def get_http_header(url):
    global USER_DATA

    url = urlparse.urlparse(url)
    path = url.path
    if path == "":
        path = "/"
    header = 'GET %s HTTP/1.1\r\n' % (path)
    header += 'Host: %s\r\n' % (url.hostname)
    header += 'Connection: keep-alive\r\n'
    header += 'Cache-Control: max-age=0\r\n'
    header += 'Accept: text/html,application/xhtmlxml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
    header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
    header += "\r\n"
    print 'header length: ' + str(len(header)) 
    print header
    USER_DATA += header


def get_dst_mac_addr(target, sourceipaddress):
    global DST_MAC
    # create packet
    interface = 'eth0'
    eth_hdr = pack("!6s6s2s", '\xff\xff\xff\xff\xff\xff', SRC_MAC.replace(':','').decode('hex'), '\x08\x06')                
    arp_hdr = pack("!2s2s1s1s2s", '\x00\x01', '\x08\x00', '\x06', '\x04', '\x00\x01')          
    arp_sender = pack("!6s4s", SRC_MAC.replace(':','').decode('hex'), socket.inet_aton(sourceipaddress))
    arp_target = pack("!6s4s", '\x00\x00\x00\x00\x00\x00', socket.inet_aton(target))
    while len(DST_MAC) == 0:
        try:
            # send packet
            s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
            s.bind((interface, socket.htons(0x0806)))
            s.send(eth_hdr + arp_hdr + arp_sender + arp_target)
            
            # wait for response
            s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
            s.settimeout(0.5)
            response = s.recvfrom(2048)
            responseMACraw = binascii.hexlify(response[0][6:12])
            responseMAC = ":".join(responseMACraw[x:x+2] for x in xrange(0, len(responseMACraw), 2))
            responseIP = socket.inet_ntoa(response[0][28:32])
            if target == responseIP:
                DST_MAC = responseMAC
                print "Response from the mac %s on IP %s" % (responseMAC, responseIP)
        except socket.timeout:
            print 'timeout'
            time.sleep(1)

def main():
    global GATEWAYIP
    global SRC_MAC
    global DST_MAC

    GATEWAYIP = get_default_gateway_linux()
    SRC_MAC = get_local_mac_addr()
    # now start constructing the packet
    url = ''
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'http://david.choffnes.com/classes/cs4700sp15/2MB.log'
    packet = ''
    source_ip = get_local_ip_addr()
    if source_ip == '':
        print 'can not get ip_addr'
        exit(1)
    print 'source_ip ' + source_ip
    # dest_ip = '192.168.1.1' # or socket.gethostbyname('www.google.com')
    # url = 'http://david.choffnes.com'
    # url = 'http://stackoverflow.com/questions/13405397/java-socket-client-sending-extra-bytes-to-device'
    purl = urlparse.urlparse(url)
    dest_ip = socket.gethostbyname(purl.hostname)
    print 'dest_ip ' + dest_ip
    get_dst_mac_addr(GATEWAYIP, source_ip)

    print GATEWAYIP
    print DST_MAC
    print SRC_MAC

    send_to_dest(url, source_ip, dest_ip)
    data = ''
    for k in sorted(DATA_RCVD.keys()):
        data += DATA_RCVD.get(k)
    cnt = data.find('\r\n\r\n')
    data = data[cnt+4:]
    # print data
    filename = 'index.html'
    if '/' in purl.path:
        path = purl.path.split('/')
        if path[-1] != '':
            filename = path[-1]

    if '.' in filename and filename.split('.')[1] in ['html', 'htm']:
        pos = 0
        chunked = ''
        now = 0
        while pos < len(data):
            pos = data.find('\r\n', now)
            try:
                chunked += data[pos+2 : pos + 2 + int(data[now:pos], 16)]
                now = pos + int(data[now:pos], 16) + 4
            except ValueError:
                break
        f = open(filename, 'w')
        f.write(chunked)
        f.close()
    else:
        f = open(filename, 'wb')
        f.write(data)
        f.close()
    for s in ALL_PACKS: 
        print s

if __name__ == '__main__':
    main()














