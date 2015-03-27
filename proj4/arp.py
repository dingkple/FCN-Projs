#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""

import socket, struct, sys, binascii, thread, time, commands, random
from struct import *



BASE_SEQ = 0
CSEQ_NUM = 0
SSEQ_NUM = 0
CACK_NUM = 0
SACK_NUM = 0

MSS = 1400




DATA_RCVD = {}
USER_DATA = ' '
LAST_RCVD_TIME = {}
SENT_PKT ={}
CWD = 1

SRC_PORT = random.randint(30000, 60000)
# if len(sys.argv) == 2 :
#     interface = sys.argv[1]
# else: #no values defined print help
#     print "Usage: %s [interface] \n   eg: %s eth0" % (sys.argv[0],sys.argv[0])
#     exit(1)

interface = 'eth0'

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


def get_local_ip_addr():
    ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | " +
                         "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
    for ip in ips.split():
        if ip[:3] != '127':
            source_ip = ip
            return ip
    self.source_ip = ''

def get_local_ip_mask():
    ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | " +
                         "awk {'print $4'} | sed -ne 's/Mask\:/ /p'")
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

            return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

def get_local_mac_addr():
    # ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'
    ips = commands.getoutput("/sbin/ifconfig eth0 | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'")
    for ip in ips.split():
        if ip[:3] != '127':
            source_ip = ip
            return ip
    self.source_ip = ''



# sourceipaddress = networkdetails[2][0]['addr']
# sourcemacaddress = networkdetails[17][0]['addr']

sourceipaddress = get_local_ip_addr()
print sourceipaddress
sourcemacaddress = get_local_mac_addr()
print sourcemacaddress
print get_default_gateway_linux()

print 'mask: ',
print get_local_ip_mask()

destinationmacaddress = ''


def construct_ip_header(source_ip, dest_ip):
    ip_ihl = 5
    ip_ver = 4
    ip_tos = 0
    
    #Id of this packet
    ip_id = 39853   
    ip_frag_off = 0
    ip_ttl = 255
    ip_proto = socket.IPPROTO_TCP

    #os will fill the following two field
    ip_tot_len = 40
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

    return ip_header


def construct_packet(source_ip, dest_ip, user_data, seq, ack, ptype, withfin = 0):
    global CSEQ_NUM
    global SSEQ_NUM
    print ptype,
    print seq,
    print ack
    ip_header = construct_ip_header(source_ip, dest_ip)
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
    tcp_window = socket.htons(10)    #   maximum allowed window size
    tcp_check = 0
    tcp_urg_ptr = 0
     
    tcp_offset_res = (tcp_doff << 4) + 0
    tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
    # the ! in the pack format string means network order
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
    packet = ip_header + tcp_header + user_data
    CSEQ_NUM += len(user_data)
    SENT_PKT[CSEQ_NUM] = [time.time(), user_data, seq, ack]
    return packet

def construct_frame_header(srcmac, dstmac):
    print 'coconstruct_frame_headerns: ',
    print srcmac,
    print dstmac
    eth_hdr = struct.pack("!6s6s2s", dstmac.replace(':', '').decode('hex'), srcmac.replace(':','').decode('hex'), '\x08\x00')  
    # dst_hdr = struct.pack("!6s6s2s", '\xff\xff\xff\xff\xff\xff', dstmac.replace(':', '').decode('hex'), '\x08\x00')

    pack = eth_hdr
    print struct.unpack("!6s6s2s", pack)
    return pack   


def worker_thread(target, sourceipaddress, sourcemacaddress):
    global destinationmacaddress
    # create packet
    eth_hdr = struct.pack("!6s6s2s", '\xff\xff\xff\xff\xff\xff', sourcemacaddress.replace(':','').decode('hex'), '\x08\x06')                
    arp_hdr = struct.pack("!2s2s1s1s2s", '\x00\x01', '\x08\x00', '\x06', '\x04', '\x00\x01')          
    arp_sender = struct.pack("!6s4s", sourcemacaddress.replace(':','').decode('hex'), socket.inet_aton(sourceipaddress))
    arp_target = struct.pack("!6s4s", '\x00\x00\x00\x00\x00\x00', socket.inet_aton(target))
    try:
        # send packet
        rawSocket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        rawSocket.bind((interface, socket.htons(0x0806)))
        rawSocket.send(eth_hdr + arp_hdr + arp_sender + arp_target)
        
        # wait for response
        rawSocket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        rawSocket.settimeout(0.5)
        response = rawSocket.recvfrom(2048)
        responseMACraw = binascii.hexlify(response[0][6:12])
        responseMAC = ":".join(responseMACraw[x:x+2] for x in xrange(0, len(responseMACraw), 2))
        responseIP = socket.inet_ntoa(response[0][28:32])
        if target == responseIP:
            destinationmacaddress = responseMAC
            print "Response from the mac %s on IP %s" % (responseMAC, responseIP)
    except socket.timeout:
        print 'timeout'
        time.sleep(1)

source_ip = '10.211.55.6'
dest_ip = '216.97.236.245'

worker_thread('10.211.55.1', sourceipaddress, sourcemacaddress)

print sourcemacaddress
print destinationmacaddress

packet = construct_frame_header(sourcemacaddress, destinationmacaddress) + construct_packet(source_ip, dest_ip, '', random.randint(0, 65536), 0, 'syn')

try:
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.settimeout(180)
except socket.error, msg:
    print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
s.bind(('eth0', 0))
s.send(packet)
        
# for i in range(256):
#     target = "10.211.55." + str(i)
#     thread.start_new_thread(worker_thread, (target, sourceipaddress, sourcemacaddress))
#     time.sleep(0.2)