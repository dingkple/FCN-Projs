#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""

from IP import *
from struct import *
import random
import socket
import urlparse
import sys
import time
import re
import os 


MSS = 1450

MAX_WIN_SIZE = 30000

# DEBUG = True
DEBUG = False

RETURN_THRESH = 0


TCP_STATE_CLOSED = 0
TCP_STATE_LISTEN = 1
TCP_STATE_SYN_SENT = 2
TCP_STATE_SYN_RCVD = 3
TCP_STATE_ESTABLISHED = 4
TCP_STATE_CLOSE_WAIT = 5
TCP_STATE_LAST_ACK = 6
TCP_STATE_FIN_WAIT_1 = 7
TCP_STATE_FIN_WAIT_2 = 8
TCP_STATE_CLOSING = 9
TCP_STATE_TIME_WAIT = 10






class raw_TCP:
    """TCP implementation by raw sockets"""
    def __init__(self):
        self.ip = raw_ip()
        self.client_seq = random.randint(0, 65536)
        self.client_ack = self.client_seq
        self.base_seq = self.client_seq
        self.client_ack = 0
        self.server_seq = 0
        self.dest_ip = ''
        self.sent_packets = {}
        self.data_buffer = ' '
        self.cwd_size = 1
        self.port = random.randint(30000, 60000)
        self.shake_finished = False
        self.last_recv_time = 0
        self.data_recved = {}
        self.result = []
        self.recv_len = 0
        self.pkt_added = []
        self.chunked = False
        self.content_length = -1
        self.htmlStarted = False

        self.fileWriter = open('temp.temp', 'w')
        self.http_data_start = False


        self.tcpState = TCP_STATE_CLOSED


    #decode information from tcp headers
    def _decode_tcp_header(self, packet, mapRet):
        # mapRet = {}
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
        mapRet['data'] = packet[20:]
        return mapRet

    # construct tcp flag for header
    def _construct_flags(self, ftype):
        tcp_rst = 0
        tcp_urg = 0
        tcp_fin = 0
        tcp_syn = 0
        tcp_psh = 0
        tcp_ack = 0
        if ftype == 'syn':
            tcp_syn = 1
        elif ftype == 'ack_syn' or ftype == 'ack': 
            tcp_ack = 1
        elif ftype == 'send':
            tcp_ack = 1
            tcp_psh = 1
        elif ftype == 'fin_ack':
            tcp_fin = 1
            tcp_ack = 1
        elif ftype == 'ack_fin':
            tcp_ack = 1
        tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
        return tcp_flags


    # construct tcp header
    def _construct_tcp_header(self, user_data, ftype, seq = -1, ack = -1):
        if seq == -1 or ack == -1:
            seq = self.client_seq
            ack = self.server_seq
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        tcp_dest = 80   # destination port
        tcp_window = socket.htons(20000)    #   maximum allowed window size
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_flags = self._construct_flags(ftype)
        tcp_seq = seq
        tcp_ack_seq = ack
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_header = pack('!HHLLBBHHH', self.port, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, 
            tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
        source_address = socket.inet_aton(self.ip.ethernet.src_ip_addr)
        dest_address = socket.inet_aton(self.dest_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(user_data)
        psh = pack('!4s4sBBH', source_address, dest_address , placeholder , protocol , tcp_length)
        psh = psh + tcp_header + user_data;
        tcp_check = checksum(psh)
        tcp_header = pack('!HHLLBBH' , self.port, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) 
        tcp_header += pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
        packet = tcp_header + user_data
        self.client_seq += len(user_data)
        if ftype == 'send':
            self.sent_packets[self.client_seq] = [time.time(), user_data, self.client_seq - len(user_data), self.server_seq]
        return packet

    # get data from buffer to send, controled by congestion window_size adv_win size
    def _get_user_data(self):
        cur_seq = self.client_seq - self.base_seq
        acked = self.client_ack - self.base_seq
        available_size = min([self.cwd_size * MSS - acked, len(self.data_buffer) - cur_seq, MAX_WIN_SIZE, MSS])
        if DEBUG:
            print cur_seq,
        if DEBUG:
            print available_size
        current_data = self.data_buffer[cur_seq: cur_seq + available_size]
        res = ''
        if len(current_data) > MSS:
            res = current_data[:MSS]
            current_data = current_data[MSS:]
        else:
            res = current_data + ''
            current_data = ''
        if len(res) % 2 != 0:
            res += ' '
        if DEBUG:
            print 'length: ' + str(len(res))
        return res

    # send packets based on the type of packets
    def _send_packet(self, ftype, retransmit = -1):
        packet = ''
        if retransmit != -1:
            print 'start retransmit: ' + str(retransmit)
            packet = self._construct_tcp_header(
                self.sent_packets.get(retransmit)[1],
                'send',
                self.sent_packets.get(retransmit)[2],
                self.sent_packets.get(retransmit)[3])
            self.ip.sent_packets(self.dest_ip, packet)

        elif ftype == 'syn':
            if DEBUG:
                print 'send syn'
            packet = self._construct_tcp_header('', 'syn')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack_syn':
            packet = self._construct_tcp_header('', 'ack_syn')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack':
            data = self._get_user_data()
            if DEBUG:
                print data
            if len(data) > 0:
                packet = self._construct_tcp_header(data, 'send')
            else:
                packet = self._construct_tcp_header(data, 'ack')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'fin_ack':
            if DEBUG:
                print 'finishing: '
            packet = self._construct_tcp_header('', 'fin_ack')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack_fin':
            if DEBUG:
                print 'ack_fin'
            packet = self._construct_tcp_header('', 'ack_fin')
            self.ip.send_packet(self.dest_ip, packet)

    # recv a packet from ip layer, filter out the packets not valid
    def _recv_packet(self):
        now = time.time()
        while True:
            cur = time.time()
            if cur - now > 180:
                if DEBUG:
                    print 'tcp error'
                sys.exit()
            if cur - now % 10 > 5:
                if DEBUG:
                    print 'tcp no data for %ds' % (cur - now)
                # continue
            mapRet, resp_packet = self.ip.receive_packet(self.dest_ip)
            if DEBUG:
                print 'got ip packet'
            if len(resp_packet) > 0:
                self.last_recv_time = time.time()
                response = self._decode_tcp_header(resp_packet, mapRet)
                if self.tcp_incoming_checksum(resp_packet, response) != 0:
                    continue
                if DEBUG:
                    print 'dst_port' + ' ' + str(response.get('dst_port'))
                if DEBUG:
                    print 'src_port' + ' ' + str(self.port)
                if response.get('dst_port') == self.port:
                    if DEBUG:
                        print 'got right port'
                    # self.client_ack = resp_packetonse.get('ack_num')
                    # self.server_seq = response.get('seq_num')
                    return response
                else:   
                    if DEBUG:
                        print 'port err ' + str(response.get('src_port')) + str(self.port)

    # check the incoming tcp packets
    def tcp_incoming_checksum(self, packet, response):
        srcaddr = socket.inet_aton(response.get('srcaddr'))
        dstaddr = socket.inet_aton(response.get('dstaddr'))
        protocol = socket.IPPROTO_TCP
        tcpLen = len(packet)
        psh = pack('!4s4sBBH', srcaddr, dstaddr, 0, protocol, tcpLen)
        psh = psh + packet
        return incoming_tcp_checksum(psh)

    # check if there's packet need retransmission
    def _check_retransmit(self):
        if DEBUG:
            print 'check for retransmit',
            print len(self.sent_packets),
            print self.sent_packets
        for pkt in self.sent_packets.keys():
            now = time.time()
            if now - self.sent_packets.get(pkt)[0] > 60:
                if DEBUG:
                    print 'preparing retransmit'
                self.cwd_size = 1
                self._send_packet('ack', pkt)
        if DEBUG:
            print 'end retransmit'

    # perform a hand shake, when it ends, tcp state should be TCP_STATE_ESTABLISHED or
    # it times out
    def _hand_shake(self):
        if self.tcpState == TCP_STATE_CLOSED:
            response = {}
            self._send_packet('syn')
            self.tcpState = TCP_STATE_SYN_SENT
            sec = time.time()
            while self.tcpState != TCP_STATE_ESTABLISHED:
                cur_sec = time.time()
                if cur_sec - sec > 180:
                    if DEBUG:
                        print 'timeout'
                    sys.exit()
                response = self._recv_packet()
                print response.get('ack')
                print response.get('syn')
                if response.get('ack') and response.get('syn') == 1:
                    if DEBUG:
                        print 'get syn_ack'
                    self.client_seq = response.get('ack_num')
                    self.server_seq = response.get('seq_num')
                    self.base_server_seq = response.get('seq_num')
                    self.server_seq += 1
                    self._send_packet('ack_syn')
                    self.tcpState = TCP_STATE_ESTABLISHED

    # fetch data from ip layer, only return the http layer right order packets
    def _fetch_data(self):
        while True:
            self._check_retransmit()
            response = self._recv_packet()
            if response.get('ack') == 1 and response.get('psh') == 1:
                ack_num = response.get('ack_num')
                if ack_num in self.sent_packets.keys():
                    del self.sent_packets[ack_num]
                seq = response.get('seq_num')
                if seq >= self.server_seq:
                    self.data_recved[response.get('seq_num')] = response.get('data')
                else:
                    if DEBUG:
                        print 'dup pkt'
                self._ack(response)
            elif response.get('ack') == 1 and response.get('fin') == 1:
                if DEBUG:
                    print 'tearing down'
                self.tcpState = TCP_STATE_CLOSE_WAIT
                self.server_seq = response.get('seq_num')
                self.client_ack = response.get('ack_num')
                self._start_tear_down()
                break
            if len(self.result) > RETURN_THRESH:
                return ''.join(self.result)
        return ''.join(self.result)
        
    # return packets in right order to caller
    def recv(self):
        self.result = []
        if self.tcpState != TCP_STATE_ESTABLISHED:
            print 'tcp state err',
            print self.tcpState
            sys.exit()
        return self.server_seq - self.base_server_seq, self._fetch_data()

    # tear down the tcp connection when fin_ack received
    def _start_tear_down(self):
        if DEBUG:
            print self.client_ack
        self.server_seq += 1
        if DEBUG:
            print self.client_ack,
        if DEBUG:
            print self.server_seq
        self._send_packet('fin_ack')

    # add the data in right order to return buffer and send ack msg
    def _ack(self, response):
        seq = response.get('seq_num')
        if DEBUG:
            print seq

        while seq in self.data_recved.keys()\
            and self.server_seq == seq:
            data = self.data_recved.get(seq)
            data_len = len(data)
            self.result.append(data)
            del self.data_recved[seq]
            self.server_seq += data_len
            seq = self.server_seq
            self.cwd_size += 1
            self._send_packet('ack')

    # close a tcp actively
    def init_tear_down(self):
        if DEBUG:
            print 'init tear down'
        self._send_packet('fin_ack')
        self.tcpState = TCP_STATE_FIN_WAIT_1
        sec = time.time()
        while True:
            if DEBUG:
                print 'waiting to fin'
            cur_sec = time.time()
            if cur_sec - sec > 180:
                if DEBUG:
                    print 'timeout'
                sys.exit()
            response = self._recv_packet()
            if response.get('fin') == 1 and response.get('ack') == 1:
                self.client_seq += 1
                self.server_seq += 1
                self._send_packet('ack_fin')
                if DEBUG:
                    print 'ack_fin sent'
                break

    # send given requests to given host 
    def send(self, url, data):
        # try:
        self.dest_ip = socket.gethostbyname(url.hostname)
        self.data_buffer += data
        if DEBUG:
            print 'started:',
            print self.dest_ip
            print self.data_buffer
        # return self._start_communicating()
        while self.tcpState != TCP_STATE_ESTABLISHED:
            self._hand_shake()
        self._send_packet('ack')
        # except:
        #     # print e
        #     print 'url error'
        #     sys.exit(0)

    # return true if the tcp state is not TCP_STATE_ESTABLISHED
    def is_closed(self):
        return self.tcpState != TCP_STATE_ESTABLISHED 

# FOR TESTING

def get_http_header(url):
    # global USER_DATA

    url = urlparse.urlparse(url)
    path = url.path
    if path == "":
        path = "/"
    header = 'GET %s HTTP/1.1\r\n' % (path)
    header += 'Host: %s\r\n' % (url.hostname)
    header += 'Connection: keep-alive\r\n'
    # header += 'Cache-Control: max-age=0\r\n'
    # header += 'Accept: text/html,application/xhtmlxml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
    # header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
    # header += 'User-Agent: HTTPTool/1.0\r\n'
    header += "\r\n"
    if DEBUG:
        print 'header length: ' + str(len(header)) 
    if DEBUG:
        print header
    return header

if __name__ == '__main__':
    url = 'http://david.choffnes.com'
    purl = urlparse.urlparse(url)
    dest_ip = socket.gethostbyname('david.choffnes.com')
    t = raw_TCP()
    # t._hand_shake()
    data = get_http_header('http://david.choffnes.com')
    t.dest_ip = socket.gethostbyname(purl.hostname)
    t.data_buffer += data
    t.send(purl, data)
    while not t.is_closed():
        l,d = t.recv()





        