#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""

import socket, struct, sys, binascii, thread, time, commands, random
from struct import *

DEBUG = False


class ethernet:
    """Get the local macaddr and dst addr"""
    def __init__(self):  
        self.src_ip_addr = self.get_local_ip_addr()
        self.src_mac_addr = self.get_local_mac_addr()
        self.interface = self.get_interface()
        gateway_ip = self.get_default_gateway_linux()
        self.gateway_mac_addr = self.get_target_mac_addr(gateway_ip)
        self.frame_header = self.construct_frame_header()
        self.send_sock = None
        self.recv_sock = None
        self.create_send_sock()
        self.create_recv_sock()

    # get local MAC address
    def get_local_mac_addr(self):
        ips = commands.getoutput("/sbin/ifconfig | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}'")
        for ip in ips.split():
            if ip[:3] != '127':
                source_ip = ip
                return ip
        self.source_ip = ''

    # get gateway ip address, used for ARP msg
    def get_default_gateway_linux(self):
        """Read the default gateway directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return socket.inet_ntoa(pack("<L", int(fields[2], 16)))

    # get the interface name for the socket to bind
    def get_interface(self):
        # ips = commands.getoutput("/sbin/ifconfig | grep -i \"Link encap\" ")
        ips = commands.getoutput("/sbin/ifconfig")
        ips = ips.split(')\n')
        for s in ips:
            if self.src_mac_addr in s:
                return s.split()[0]

    # get current ip address
    def get_local_ip_addr(self):
        ips = commands.getoutput("/sbin/ifconfig | grep -i \"inet\" | grep -iv \"inet6\" | " +
                             "awk {'print $2'} | sed -ne 's/addr\:/ /p'")
        for ip in ips.split():
            if ip[:3] != '127':
                source_ip = ip
                return ip
        self.source_ip = ''

    # construct header for every frame, destination MAC address + source MAC address + '0x0800'
    def construct_frame_header(self):
        if DEBUG: 
            print 'coconstruct_frame_headerns: '
        frame_packet = pack("!6s6s2s", self.gateway_mac_addr.replace(':', '').decode('hex'), self.src_mac_addr.replace(':','').decode('hex'), '\x08\x00') 
        return frame_packet

    # create SEND socket for AF_PACKET
    def create_send_sock(self):
        try:
            self.send_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
            self.send_sock.bind((self.interface, 0))
        except socket.error, msg:
            if DEBUG: 
                print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()

    # create RECV socket for AF_PACKET
    def create_recv_sock(self):
        try:
            self.recv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
            # self.recv_sock.setblocking(0)
            # self.recv_sock.bind((INTERFACE, 0))
        except socket.error , msg:
            if DEBUG: 
                print 'recv error'
            if DEBUG: 
                print 'Socket could not be created. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()

    # get gateway's MAC address by ARP
    def get_target_mac_addr(self, target):
        flag = False
        while not flag:
            #constructing ARP packet
            eth_hdr = pack("!6s6s2s", '\xff\xff\xff\xff\xff\xff', self.src_mac_addr.replace(':','').decode('hex'), '\x08\x06')
            arp_hdr = pack("!2s2s1s1s2s", '\x00\x01', '\x08\x00', '\x06', '\x04', '\x00\x01')          
            arp_sender = pack("!6s4s", self.src_mac_addr.replace(':','').decode('hex'), socket.inet_aton(self.src_ip_addr))
            arp_target = pack("!6s4s", '\x00\x00\x00\x00\x00\x00', socket.inet_aton(target))
            try:
                # send arp packet
                s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
                s.bind((self.interface, socket.htons(0x0806)))
                s.send(eth_hdr + arp_hdr + arp_sender + arp_target)
                
                # wait for gateway's response
                s = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
                s.settimeout(0.5)
                response = s.recvfrom(2048)
                responseMACraw = binascii.hexlify(response[0][6:12])
                responseMAC = ":".join(responseMACraw[x:x+2] for x in xrange(0, len(responseMACraw), 2))
                responseIP = socket.inet_ntoa(response[0][28:32])
                if target == responseIP and len(responseMAC) > 0:
                    flag = not flag
                    if DEBUG: 
                        print responseMAC
                    if DEBUG: 
                        print "Response from the mac %s on IP %s" % (responseMAC, responseIP)
                    return responseMAC
            except socket.timeout:
                if DEBUG: 
                    print 'timeout'
                time.sleep(1)

    # add frame header and send packet
    def send(self, packet):
        if DEBUG: 
            print len(packet)
        packet = self.frame_header + packet
        if DEBUG: 
            print len(packet)
        self.send_sock.send(packet)

    # receive packet and filter out the packet with the right MAC address
    def recv(self):
        while True:
            packet = self.recv_sock.recvfrom(65536)[0]
            if len(packet) > 14:
                if DEBUG: 
                    print len(packet)
                fh = packet[:14]
                dst_mac = self.gateway_mac_addr.replace(':','').decode('hex')
                src_mac = self.src_mac_addr.replace(':','').decode('hex')
                if (fh[:6] == src_mac
                    and fh[6:12] == dst_mac):
                    if DEBUG: 
                        print 'found'
                    return packet[14:]


if __name__ == '__main__':
    #for test
    e = ethernet()
    # print e.interface
    for v in vars(e):
        if DEBUG: 
            print v,
        if DEBUG: 
            print getattr(e, v)




