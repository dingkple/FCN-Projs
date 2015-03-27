#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""


import Ethernet
import random
from utilities import *
import raw_sock
from struct import *
import socket
import time

DEBUG = False


class raw_ip:

    def __init__(self):
        self.ethernet = Ethernet.ethernet()


    # decode the IP part of the packet
    def decodeIpHeader(self, packet):
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

    # construct the 
    def construct_header(self, dest_ip, tcp_data):
        if DEBUG:
            print 'ip header building: '
        ip_ihl = 5
        ip_ver = 4
        ip_tos = 0
        #Id of this packet
        ip_id = random.randint(0, 65536)
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP

        #os will fill the following two field
        ip_tot_len = 20 + len(tcp_data)
        if DEBUG:
            print 'ip total len: ' + str(ip_tot_len)
        ip_check = 0

        ip_saddr = socket.inet_aton (self.ethernet.src_ip_addr)   
        ip_daddr = socket.inet_aton (dest_ip)   
        ip_ihl_ver = (ip_ver << 4) + ip_ihl
        
        ip_header = pack('!BBHHHBBH4s4s' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, 
        ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        cs = checksum(ip_header)

        ip_check = cs & 0xffff

        ip_header = pack('!BBHHHBB' , ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, 
            ip_ttl, ip_proto)
        ip_header += pack('H', ip_check) + pack('!4s4s', ip_saddr, ip_daddr)

        return ip_header + tcp_data



    def send_packet(self, dest_ip, data):

        packet = self.construct_header(dest_ip, data)
        if DEBUG:
            print 'ip sending: ' + str(len(packet))
        self.ethernet.send(packet)


    def receive_packet(self, dest_ip):
        now = time.time()
        while True:
            cur = time.time()
            if cur - now > 2:
                if DEBUG:
                    print 'timeout'
                return -1, -1
            received_packet = self.ethernet.recv()
            if DEBUG:
                print 'ip decoding'
            ip_header = received_packet[0:20]
            iph = unpack('!BBHHHBBH4s4s' , ip_header)
            if checksum(ip_header) != 0:
                if DEBUG:
                    print checksum(ip_header)
                continue
            mapIpTmp = self.decodeIpHeader(ip_header)
            if (mapIpTmp.get('protocol') != socket.IPPROTO_TCP
                or not mapIpTmp.has_key('srcaddr') or not mapIpTmp.get('srcaddr') == dest_ip
                or not mapIpTmp.has_key('dstaddr') or not mapIpTmp.get('dstaddr') == self.ethernet.src_ip_addr):
                if DEBUG:
                    print 'fail ip checking'
                continue
            tcp_data = received_packet[20:]
            if DEBUG:
                print 'ip returned'
            return mapIpTmp, tcp_data





if __name__ == '__main__':
    tip = raw_ip()

    source_ip = tip.ethernet.src_ip_addr
    dest_ip = socket.gethostbyname('david.choffnes.com')
    user_data = ''
    seq = random.randint(0, 65536)
    ack = 0
    ptype = 'syn'
    packet = raw_sock.construct_packet(source_ip, dest_ip, user_data, seq, ack, ptype)
    tip.send_packet(dest_ip, packet[34:])
    tip.receive_packet(dest_ip)



























